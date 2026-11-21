"""
JalRakshak NCR — Fleet Logistics & Transponder Router (Phase 3)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.fleet_service import fleet_service
from routers.auth_router import get_current_user, require_roles
from websocket_manager import ws_manager

router = APIRouter(prefix="/api/v1/fleet", tags=["Emergency Vehicle Fleet"])

class TransponderPingRequest(BaseModel):
    lat: float = Field(..., description="WGS84 Latitude")
    lng: float = Field(..., description="WGS84 Longitude")
    speed_kmh: float = Field(default=0.0, description="Current speed in km/h")
    heading_deg: float = Field(default=0.0, description="Compass heading in degrees (0-360)")
    current_route: Optional[str] = Field(default=None, description="Optional active route note")

class VehicleStatusChangeRequest(BaseModel):
    status: str = Field(..., description="New operational status: 'OPEN', 'OCCUPIED', 'MAINTENANCE'")
    route_note: Optional[str] = Field(default=None, description="Optional status annotation")

@router.get("")
def list_fleet_vehicles(
    category: Optional[str] = Query(None, description="Filter category: 'TANKER', 'AMBULANCE', 'BOAT', 'QRV'"),
    status: Optional[str] = Query(None, description="Filter status: 'OPEN', 'OCCUPIED', 'MAINTENANCE'"),
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE", "TRAFFIC_POLICE"]))
):
    """Returns emergency vehicles inventory with live transponder coordinates."""
    vehicles = fleet_service.get_all_vehicles(category=category, status=status)
    return {
        "count": len(vehicles),
        "total_fleet": 8,
        "vehicles": vehicles
    }

@router.get("/nearest-unit")
def find_nearest_vehicle(
    lat: float = Query(..., description="Target Latitude"),
    lng: float = Query(..., description="Target Longitude"),
    category: Optional[str] = Query(None, description="Optional category restriction")
):
    """Calculates spatial nearest-unit distance and transit ETA using Haversine algorithm."""
    nearest = fleet_service.find_nearest_open_vehicle(lat, lng, category)
    if not nearest:
        raise HTTPException(status_code=404, detail="No available 'OPEN' vehicles found in fleet.")
    return nearest

@router.get("/{vehicle_id}")
def get_vehicle_detail(vehicle_id: str):
    """Lookup vehicle profile and active transponder coordinates."""
    vehicle = fleet_service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return vehicle

@router.post("/{vehicle_id}/transponder")
async def receive_transponder_ping(vehicle_id: str, req: TransponderPingRequest):
    """
    Ingests live GPS ping from vehicle transponder or driver field tablet.
    Broadcasts real-time movement onto official GIS command map over WebSockets.
    """
    updated = fleet_service.update_transponder_gps(
        vehicle_id=vehicle_id,
        lat=req.lat,
        lng=req.lng,
        speed_kmh=req.speed_kmh,
        heading_deg=req.heading_deg,
        current_route=req.current_route
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")

    # Real-time WebSocket broadcast to official command dashboard
    await ws_manager.broadcast_to_officials("vehicle:location_broadcast", updated)
    return {"status": "transponder_updated", "vehicle": updated}

@router.patch("/{vehicle_id}/status")
def change_vehicle_status(
    vehicle_id: str,
    req: VehicleStatusChangeRequest,
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE"]))
):
    """Updates vehicle availability status."""
    valid_statuses = ("OPEN", "OCCUPIED", "MAINTENANCE")
    if req.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}."
        )

    updated = fleet_service.set_vehicle_status(vehicle_id, req.status, req.route_note)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Vehicle '{vehicle_id}' not found.")
    return {"status": "updated", "vehicle": updated}
