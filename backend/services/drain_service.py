"""
JalRakshak NCR — Master 36 Stormwater Drains & Desilting Audit Service (Phase 2)
Engineered for Team NeerNetra (SustainX 2026)
Governs all 36 critical municipal drainage trunk conduits across:
Leg 1 (East Golf Course), Leg 2 (Central Spine & Old Gurugram), and Leg 3 (Badshahpur Master Trunk).
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import get_db_connection

class DrainService:
    @staticmethod
    def get_all_drains(leg: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all 36 stormwater drains with optional leg/status filters."""
        conn = get_db_connection()
        query = "SELECT * FROM stormwater_drains WHERE 1=1"
        params = []

        if leg:
            query += " AND catchment_leg LIKE ?"
            params.append(f"%{leg}%")
        if status:
            query += " AND status = ?"
            params.append(status.upper())

        query += " ORDER BY id ASC;"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_drain_by_id(drain_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves single drain record along with its inspection audit proofs."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM stormwater_drains WHERE id = ? OR code = ?;", (drain_id, drain_id)).fetchone()
        if not row:
            conn.close()
            return None

        drain = dict(row)
        audits = conn.execute("SELECT * FROM desilting_audit_logs WHERE drain_id = ? ORDER BY logged_at DESC;", (drain["id"],)).fetchall()
        conn.close()
        drain["audit_logs"] = [dict(a) for a in audits]
        return drain

    @staticmethod
    def get_drain_summary() -> Dict[str, Any]:
        """Calculates city-wide desilting progress across all 36 master drains."""
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM stormwater_drains;").fetchall()
        conn.close()

        total = len(rows)
        cleaned_count = sum(1 for r in rows if r["status"] in ("CLEANED", "VERIFIED"))
        progress_count = sum(1 for r in rows if r["status"] == "DESILTING_IN_PROGRESS")
        clogged_count = sum(1 for r in rows if r["status"] == "CLOGGED")

        pct_cleaned = int(round((cleaned_count / total) * 100)) if total > 0 else 0
        total_dredged_m3 = sum(float(r["dredged_volume_m3"]) for r in rows)
        total_target_m3 = sum(float(r["target_volume_m3"]) for r in rows)

        # By Drainage Leg breakdown
        leg1_cleaned = sum(1 for r in rows if "LEG 1" in r["catchment_leg"] and r["status"] in ("CLEANED", "VERIFIED"))
        leg2_cleaned = sum(1 for r in rows if "LEG 2" in r["catchment_leg"] and r["status"] in ("CLEANED", "VERIFIED"))
        leg3_cleaned = sum(1 for r in rows if "LEG 3" in r["catchment_leg"] and r["status"] in ("CLEANED", "VERIFIED"))

        return {
            "total_drains_indexed": total,
            "cleaned_or_verified_count": cleaned_count,
            "desilting_in_progress_count": progress_count,
            "clogged_count": clogged_count,
            "city_desilting_percentage": pct_cleaned,
            "total_dredged_volume_m3": round(total_dredged_m3, 1),
            "total_target_volume_m3": round(total_target_m3, 1),
            "corridor_breakdown": {
                "leg_1_east_golf_course": f"{leg1_cleaned} / 12 Cleaned",
                "leg_2_central_spine": f"{leg2_cleaned} / 12 Cleaned",
                "leg_3_badshahpur_trunk": f"{leg3_cleaned} / 12 Cleaned"
            }
        }

    @classmethod
    def update_drain_status(cls, drain_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        """Updates drain status in database."""
        conn = get_db_connection()
        now_iso = datetime.now(timezone.utc).isoformat()
        last_cleaned = now_iso if new_status in ("CLEANED", "VERIFIED") else None
        
        conn.execute("""
        UPDATE stormwater_drains 
        SET status = ?, last_cleaned_at = COALESCE(?, last_cleaned_at), updated_at = ?
        WHERE id = ? OR code = ?;
        """, (new_status.upper(), last_cleaned, now_iso, drain_id, drain_id))
        conn.commit()
        conn.close()
        return cls.get_drain_by_id(drain_id)

    @classmethod
    def log_desilting_audit(
        cls,
        drain_id: str,
        contractor_name: str,
        dredged_volume_m3: float,
        photo_before_url: Optional[str] = None,
        photo_after_url: Optional[str] = None,
        notes: Optional[str] = None,
        inspector_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Logs contractor before/after photographic proof and increments silt removal metric."""
        drain = cls.get_drain_by_id(drain_id)
        if not drain:
            raise ValueError(f"Drain '{drain_id}' not found.")

        audit_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()

        # Insert audit proof
        conn.execute("""
        INSERT INTO desilting_audit_logs 
        (id, drain_id, contractor_name, inspector_name, dredged_volume_m3, photo_before_url, photo_after_url, verified_by_inspector, notes, logged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?);
        """, (audit_id, drain["id"], contractor_name, inspector_name or "MCG Sanitary Inspector", dredged_volume_m3, photo_before_url, photo_after_url, notes, now_iso))

        # Update drain record
        new_dredged = drain["dredged_volume_m3"] + dredged_volume_m3
        conn.execute("""
        UPDATE stormwater_drains
        SET status = 'CLEANED', dredged_volume_m3 = ?, last_cleaned_at = ?, updated_at = ?
        WHERE id = ?;
        """, (new_dredged, now_iso, now_iso, drain["id"]))
        conn.commit()
        conn.close()

        return {
            "status": "audit_logged",
            "audit_id": audit_id,
            "drain_id": drain["id"],
            "dredged_volume_m3": dredged_volume_m3,
            "new_total_dredged_m3": new_dredged,
            "status_set_to": "CLEANED"
        }

drain_service = DrainService()
