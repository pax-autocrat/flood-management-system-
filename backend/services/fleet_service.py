"""
JalRakshak NCR — Fleet Logistics & Transponder Service (Phase 3)
Engineered for Team NeerNetra (SustainX 2026)
Governs 8 Emergency Rescue Vehicles across TANKER, AMBULANCE, BOAT, and QRV categories.
Provides live GPS transponder updates, status filters, and nearest-unit spatial calculation.
"""

import os
import sys
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import get_db_connection

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)

class FleetService:
    @staticmethod
    def get_all_vehicles(category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns fleet vehicles filtered by category and/or deployment availability."""
        conn = get_db_connection()
        query = "SELECT * FROM rescue_vehicles WHERE 1=1"
        params = []

        if category and category.upper() != "ALL":
            query += " AND category = ?"
            params.append(category.upper())
        if status and status.upper() != "ALL":
            query += " AND status = ?"
            params.append(status.upper())

        query += " ORDER BY id ASC;"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_vehicle_by_id(vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Lookup single vehicle record by ID."""
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM rescue_vehicles WHERE id = ?;", (vehicle_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def update_transponder_gps(
        cls,
        vehicle_id: str,
        lat: float,
        lng: float,
        speed_kmh: float = 0.0,
        heading_deg: float = 0.0,
        current_route: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates live vehicle GPS transponder telemetry."""
        conn = get_db_connection()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        conn.execute("""
        UPDATE rescue_vehicles
        SET lat = ?, lng = ?, speed_kmh = ?, heading_deg = ?, current_route = COALESCE(?, current_route), last_ping = ?
        WHERE id = ?;
        """, (lat, lng, speed_kmh, heading_deg, current_route, now_iso, vehicle_id))
        conn.commit()
        conn.close()
        return cls.get_vehicle_by_id(vehicle_id)

    @classmethod
    def set_vehicle_status(cls, vehicle_id: str, new_status: str, route_note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Updates vehicle operational status (OPEN, OCCUPIED, MAINTENANCE)."""
        conn = get_db_connection()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        conn.execute("""
        UPDATE rescue_vehicles
        SET status = ?, current_route = COALESCE(?, current_route), last_ping = ?
        WHERE id = ?;
        """, (new_status.upper(), route_note, now_iso, vehicle_id))
        conn.commit()
        conn.close()
        return cls.get_vehicle_by_id(vehicle_id)

    @classmethod
    def find_nearest_open_vehicle(cls, target_lat: float, target_lng: float, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Executes spatial nearest-unit calculation.
        Finds the closest available 'OPEN' vehicle using the Haversine formula.
        """
        open_vehicles = cls.get_all_vehicles(category=category, status="OPEN")
        if not open_vehicles and category:
            # Fallback across all available categories if specific category is occupied
            open_vehicles = cls.get_all_vehicles(status="OPEN")
            
        if not open_vehicles:
            return None

        best_vehicle = None
        min_distance = float('inf')

        for v in open_vehicles:
            dist_km = calculate_haversine_distance_km(v["lat"], v["lng"], target_lat, target_lng)
            if dist_km < min_distance:
                min_distance = dist_km
                best_vehicle = v
                best_vehicle["distance_km"] = dist_km
                # Estimated transit time assuming 25 km/h urban flood transit speed
                best_vehicle["estimated_eta_mins"] = max(2, int(round((dist_km / 25.0) * 60)))

        return best_vehicle

fleet_service = FleetService()
