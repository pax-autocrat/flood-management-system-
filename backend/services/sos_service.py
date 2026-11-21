"""
JalRakshak NCR — Citizen SOS Incident & Dispatch Engine (Phase 3)
Engineered for Team NeerNetra (SustainX 2026)
Governs citizen emergency distress intake, automated nearest-unit spatial dispatch,
and real-time live rescue tracking.
"""

import os
import sys
import random
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import get_db_connection
from services.fleet_service import fleet_service, calculate_haversine_distance_km
from websocket_manager import ws_manager

class SosService:
    @staticmethod
    def _generate_sos_id() -> str:
        """Generates guaranteed unique SOS identifier (e.g. SOS-9F8A12)."""
        return f"SOS-{uuid.uuid4().hex[:6].upper()}"

    @classmethod
    async def create_sos_incident(
        cls,
        caller_name: str,
        caller_phone: str,
        location_name: str,
        lat: float,
        lng: float,
        issue_type: str,
        urgency: str = "HIGH",
        people_count: int = 1,
        has_medical_emergency: bool = False,
        water_level_gauge: Optional[str] = "Door Sill",
        landmark_notes: Optional[str] = None,
        hotspot_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates persistent distress ticket and broadcasts instant alarm to MCG control room."""
        sos_id = cls._generate_sos_id()
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()

        conn.execute("""
        INSERT INTO sos_incidents 
        (id, caller_name, caller_phone, hotspot_id, location_name, lat, lng, issue_type, urgency, people_count, has_medical_emergency, water_level_gauge, landmark_notes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?);
        """, (sos_id, caller_name, caller_phone, hotspot_id, location_name, lat, lng, issue_type, urgency.upper(), people_count, 1 if has_medical_emergency else 0, water_level_gauge, landmark_notes, now_iso))
        conn.commit()
        conn.close()

        created_sos = cls.get_sos_by_id(sos_id)

        # Real-time WebSocket alarm to official dashboard
        await ws_manager.broadcast_to_officials("sos:new_alert", created_sos)
        return created_sos

    @staticmethod
    def get_all_sos_requests(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all distress calls ordered by urgency and timestamp."""
        conn = get_db_connection()
        query = "SELECT s.*, v.name as assigned_vehicle_name, v.driver_phone as assigned_driver_phone FROM sos_incidents s LEFT JOIN rescue_vehicles v ON s.assigned_vehicle_id = v.id WHERE 1=1"
        params = []

        if status_filter:
            query += " AND s.status = ?"
            params.append(status_filter.upper())

        query += " ORDER BY CASE s.urgency WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, s.created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_sos_by_id(sos_id: str) -> Optional[Dict[str, Any]]:
        """Lookup distress incident by ID."""
        conn = get_db_connection()
        row = conn.execute("""
        SELECT s.*, v.name as assigned_vehicle_name, v.driver_phone as assigned_driver_phone, v.category as vehicle_category, v.lat as vehicle_lat, v.lng as vehicle_lng
        FROM sos_incidents s
        LEFT JOIN rescue_vehicles v ON s.assigned_vehicle_id = v.id
        WHERE s.id = ?;
        """, (sos_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def get_citizen_tracking_view(cls, sos_id: str) -> Optional[Dict[str, Any]]:
        """
        Builds live citizen tracking screen telemetry:
        Calculates real-time distance and arrival ETA of assigned rescue vehicle.
        """
        sos = cls.get_sos_by_id(sos_id)
        if not sos:
            return None

        tracking_data = {
            "sos_id": sos["id"],
            "caller_name": sos["caller_name"],
            "status": sos["status"],
            "location_name": sos["location_name"],
            "issue_type": sos["issue_type"],
            "reported_at": sos["created_at"],
            "assigned_vehicle": None
        }

        if sos["assigned_vehicle_id"] and sos.get("vehicle_lat") is not None:
            dist_km = calculate_haversine_distance_km(
                sos["vehicle_lat"], sos["vehicle_lng"],
                sos["lat"], sos["lng"]
            )
            eta_mins = max(1, int(round((dist_km / 25.0) * 60)))

            tracking_data["assigned_vehicle"] = {
                "vehicle_id": sos["assigned_vehicle_id"],
                "name": sos["assigned_vehicle_name"],
                "category": sos.get("vehicle_category"),
                "driver_phone": sos.get("assigned_driver_phone"),
                "current_location": {"lat": sos["vehicle_lat"], "lng": sos["vehicle_lng"]},
                "distance_km": dist_km,
                "distance_meters": int(dist_km * 1000),
                "estimated_arrival_eta_mins": eta_mins
            }

        return tracking_data

    @classmethod
    async def dispatch_vehicle(cls, sos_id: str, vehicle_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Dispatches emergency unit to distress call.
        If vehicle_id is None, automatically runs spatial nearest-unit algorithm.
        """
        sos = cls.get_sos_by_id(sos_id)
        if not sos:
            raise ValueError(f"SOS '{sos_id}' not found.")

        target_vehicle = None
        if vehicle_id:
            target_vehicle = fleet_service.get_vehicle_by_id(vehicle_id)
            if not target_vehicle:
                raise ValueError(f"Vehicle '{vehicle_id}' not found.")
        else:
            # Nearest-unit spatial auto-matching
            target_vehicle = fleet_service.find_nearest_open_vehicle(sos["lat"], sos["lng"])
            if not target_vehicle:
                raise ValueError("All rescue fleet units are currently Occupied or undergoing Maintenance.")

        # Update vehicle status to OCCUPIED
        fleet_service.set_vehicle_status(
            vehicle_id=target_vehicle["id"],
            new_status="OCCUPIED",
            route_note=f"Responding to SOS: {sos['location_name']}"
        )

        # Update SOS ticket to ASSIGNED
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        conn.execute("""
        UPDATE sos_incidents
        SET status = 'ASSIGNED', assigned_vehicle_id = ?, dispatched_at = ?
        WHERE id = ?;
        """, (target_vehicle["id"], now_iso, sos_id))
        conn.commit()
        conn.close()

        updated_sos = cls.get_sos_by_id(sos_id)
        tracking_view = cls.get_citizen_tracking_view(sos_id)

        # Notify both official dashboard and citizen tracking room
        await ws_manager.broadcast_to_officials("sos:status_change", updated_sos)
        await ws_manager.broadcast_to_room(f"citizen_{sos_id}", "sos:dispatched", tracking_view)

        return {
            "status": "dispatched",
            "sos_id": sos_id,
            "assigned_vehicle": target_vehicle["name"],
            "assigned_vehicle_id": target_vehicle["id"],
            "driver_name": target_vehicle["driver_name"],
            "driver_phone": target_vehicle["driver_phone"],
            "tracking_view": tracking_view
        }

    @classmethod
    async def resolve_sos(cls, sos_id: str) -> Dict[str, Any]:
        """Resolves distress ticket and releases assigned vehicle back to 'OPEN' ready pool."""
        sos = cls.get_sos_by_id(sos_id)
        if not sos:
            raise ValueError(f"SOS '{sos_id}' not found.")

        # Release vehicle back to OPEN
        if sos["assigned_vehicle_id"]:
            fleet_service.set_vehicle_status(
                vehicle_id=sos["assigned_vehicle_id"],
                new_status="OPEN",
                route_note="Patrol / Standby"
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_db_connection()
        conn.execute("""
        UPDATE sos_incidents
        SET status = 'RESOLVED', resolved_at = ?
        WHERE id = ?;
        """, (now_iso, sos_id))
        conn.commit()
        conn.close()

        updated_sos = cls.get_sos_by_id(sos_id)
        await ws_manager.broadcast_to_officials("sos:resolved", updated_sos)
        await ws_manager.broadcast_to_room(f"citizen_{sos_id}", "sos:resolved", {"status": "RESOLVED", "sos_id": sos_id})

        return {
            "status": "resolved",
            "sos_id": sos_id,
            "resolved_at": now_iso,
            "released_vehicle_id": sos["assigned_vehicle_id"]
        }

sos_service = SosService()
