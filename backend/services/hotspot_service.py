"""
JalRakshak NCR — Persistent Hotspot Telemetry Service (Phase 2)
Engineered for Team NeerNetra (SustainX 2026)
Manages persistent water depth telemetry, pump assignment, drain desilting impact,
and city-wide Road Safety Percentage calculations.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import get_db_connection

class HotspotService:
    @staticmethod
    def calculate_effective_depth(base_storm_depth: int, drain_cleaned: bool, pump_assigned: bool, weather_factor: float = 1.0) -> int:
        """
        Calculates effective flood depth in cm based on:
        - Weather rain intensity factor
        - Desilting discount: -40% when primary stormwater drain is cleaned
        - Submersible dewatering pump discount: -65% when 5000 GPM pump is active
        """
        depth = float(base_storm_depth) * weather_factor
        if drain_cleaned:
            depth *= 0.60  # 40% reduction
        if pump_assigned:
            depth *= 0.35  # 65% reduction
        return max(0, int(round(depth)))

    @classmethod
    def get_all_hotspots(cls, weather_factor: float = 1.0) -> List[Dict[str, Any]]:
        """Returns all persistent hotspots with dynamically computed effective water depth."""
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM hotspots_db ORDER BY current_depth_cm DESC;").fetchall()
        conn.close()

        results = []
        for r in rows:
            spot = dict(r)
            effective_depth = cls.calculate_effective_depth(
                base_storm_depth=spot["storm_depth_cm"],
                drain_cleaned=bool(spot["drain_cleaned"]),
                pump_assigned=bool(spot["pump_assigned"]),
                weather_factor=weather_factor
            )
            spot["effective_depth_cm"] = effective_depth
            
            # Passability status
            if effective_depth < 25:
                spot["status"] = "CLEAR"
                spot["status_badge"] = "SAFE_PASSABLE"
            elif effective_depth < 55:
                spot["status"] = "WATERLOGGED"
                spot["status_badge"] = "SHALLOW_WATCH"
            else:
                spot["status"] = "FLOODED"
                spot["status_badge"] = "DEEP_FLOODED_CLOSED"

            results.append(spot)
        return results

    @classmethod
    def get_hotspot_by_id(cls, spot_id: str, weather_factor: float = 1.0) -> Optional[Dict[str, Any]]:
        """Lookup single persistent hotspot by ID or Code."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM hotspots_db WHERE id = ? OR code = ?;", (spot_id, spot_id)).fetchone()
        conn.close()
        if not row:
            return None

        spot = dict(row)
        effective_depth = cls.calculate_effective_depth(
            base_storm_depth=spot["storm_depth_cm"],
            drain_cleaned=bool(spot["drain_cleaned"]),
            pump_assigned=bool(spot["pump_assigned"]),
            weather_factor=weather_factor
        )
        spot["effective_depth_cm"] = effective_depth
        spot["status"] = "CLEAR" if effective_depth < 25 else ("WATERLOGGED" if effective_depth < 55 else "FLOODED")
        return spot

    @classmethod
    def update_telemetry(cls, spot_id: str, depth_cm: int) -> Optional[Dict[str, Any]]:
        """Updates sensor telemetry depth in persistent database."""
        conn = get_db_connection()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute("""
        UPDATE hotspots_db 
        SET current_depth_cm = ?, storm_depth_cm = ?, last_updated = ?
        WHERE id = ? OR code = ?;
        """, (depth_cm, depth_cm, now_iso, spot_id, spot_id))
        conn.commit()
        conn.close()
        return cls.get_hotspot_by_id(spot_id)

    @classmethod
    def toggle_pump(cls, spot_id: str, active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Toggles dewatering pump status at hotspot."""
        conn = get_db_connection()
        spot = conn.execute("SELECT * FROM hotspots_db WHERE id = ? OR code = ?;", (spot_id, spot_id)).fetchone()
        if not spot:
            conn.close()
            return None

        new_status = (1 if active else 0) if active is not None else (0 if spot["pump_assigned"] else 1)
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute("""
        UPDATE hotspots_db SET pump_assigned = ?, last_updated = ? WHERE id = ? OR code = ?;
        """, (new_status, now_iso, spot_id, spot_id))
        conn.commit()
        conn.close()
        return cls.get_hotspot_by_id(spot_id)

    @classmethod
    def toggle_drain(cls, spot_id: str, cleaned: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Toggles primary stormwater drain cleaned status."""
        conn = get_db_connection()
        spot = conn.execute("SELECT * FROM hotspots_db WHERE id = ? OR code = ?;", (spot_id, spot_id)).fetchone()
        if not spot:
            conn.close()
            return None

        new_status = (1 if cleaned else 0) if cleaned is not None else (0 if spot["drain_cleaned"] else 1)
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute("""
        UPDATE hotspots_db SET drain_cleaned = ?, last_updated = ? WHERE id = ? OR code = ?;
        """, (new_status, now_iso, spot_id, spot_id))
        conn.commit()
        conn.close()
        return cls.get_hotspot_by_id(spot_id)

    @classmethod
    def get_road_safety_metrics(cls, weather_factor: float = 1.0) -> Dict[str, Any]:
        """Calculates municipal Road Safety Percentage across Gurugram arterial network."""
        hotspots = cls.get_all_hotspots(weather_factor)
        total = len(hotspots)
        if total == 0:
            return {"road_safety_pct": 100, "safe_count": 0, "watch_count": 0, "flooded_count": 0}

        safe_count = sum(1 for s in hotspots if s["effective_depth_cm"] < 25)
        watch_count = sum(1 for s in hotspots if 25 <= s["effective_depth_cm"] < 55)
        flooded_count = sum(1 for s in hotspots if s["effective_depth_cm"] >= 55)

        # Weighted Road Safety Percentage Formula
        safety_pct = int(round(((safe_count + (watch_count * 0.5)) / total) * 100))

        return {
            "road_safety_pct": safety_pct,
            "total_evaluated_hotspots": total,
            "breakdown": {
                "safe_wide_spots": safe_count,
                "shallow_waterlogged_spots": watch_count,
                "deep_flooded_closed_spots": flooded_count
            },
            "advisory": (
                "All wide arterial roads clear. Normal transit." if safety_pct >= 80 else (
                    "Caution: Underpasses waterlogged. Use elevated Golf Course Rd & SPR." if safety_pct >= 50 else (
                        "RED ALERT: Avoid NH-48 & major underpasses. High risk of hydrostatic engine lock."
                    )
                )
            )
        }

hotspot_service = HotspotService()
