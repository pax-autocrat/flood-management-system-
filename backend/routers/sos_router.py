"""
JalRakshak NCR — Citizen SOS Incident & Dispatch Router (Phase 3)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.sos_service import sos_service
from routers.auth_router import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/sos", tags=["Citizen SOS & Rescue Dispatch"])

class SosSubmissionRequest(BaseModel):
    caller_name: str = Field(..., description="Name of stranded citizen or caller")
    caller_phone: str = Field(..., description="Contact phone number for rescue team callback")
    location_name: str = Field(..., description="Gurugram landmark, sector, or road name")
    lat: float = Field(..., description="GPS Latitude coordinate")
    lng: float = Field(..., description="GPS Longitude coordinate")
    issue_type: str = Field(..., description="Emergency category: 'Vehicle Stuck in Deep Floodwater', 'Medical Evacuation', etc.")
    urgency: str = Field(default="HIGH", description="Urgency level: LOW, MEDIUM, HIGH, CRITICAL")
    people_count: int = Field(default=1, ge=1, description="Number of stranded individuals")
    has_medical_emergency: bool = Field(default=False, description="Flag for priority medical emergency")
    water_level_gauge: Optional[str] = Field(default="Door Sill", description="Water level relative to vehicle/person")
    landmark_notes: Optional[str] = Field(default=None, description="Specific details, service lane exit, car color, etc.")
    hotspot_id: Optional[str] = Field(default=None, description="Optional municipal hotspot code")

class DispatchRequest(BaseModel):
    vehicle_id: Optional[str] = Field(default=None, description="Specific vehicle ID, or None for spatial nearest-unit auto match")

@router.post("")
async def submit_emergency_sos(req: SosSubmissionRequest):
    """
    Submits emergency distress ticket.
    Instantly fires real-time WebSocket alarm to MCG Command Center.
    """
    created = await sos_service.create_sos_incident(
        caller_name=req.caller_name,
        caller_phone=req.caller_phone,
        location_name=req.location_name,
        lat=req.lat,
        lng=req.lng,
        issue_type=req.issue_type,
        urgency=req.urgency,
        people_count=req.people_count,
        has_medical_emergency=req.has_medical_emergency,
        water_level_gauge=req.water_level_gauge,
        landmark_notes=req.landmark_notes,
        hotspot_id=req.hotspot_id
    )
    return {
        "status": "sos_received",
        "sos_id": created["id"],
        "message": "Emergency SOS transmitted to MCG Flood Control Room.",
        "incident": created
    }

@router.get("/active")
def get_active_sos_queue(
    status_filter: Optional[str] = Query(None, description="Filter: 'PENDING', 'ASSIGNED', 'RESOLVED'"),
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE", "TRAFFIC_POLICE"]))
):
    """Returns active distress queue for municipal control room. Gated for officials."""
    queue = sos_service.get_all_sos_requests(status_filter)
    return {
        "count": len(queue),
        "queue": queue
    }

@router.get("/track/{sos_id}")
def track_citizen_sos(sos_id: str):
    """
    Public citizen rescue tracker:
    Streams live distance (km & meters) and arrival ETA of assigned rescue vehicle.
    """
    view = sos_service.get_citizen_tracking_view(sos_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"SOS incident '{sos_id}' not found.")
    return view

@router.post("/{sos_id}/dispatch")
async def dispatch_emergency_vehicle(
    sos_id: str,
    req: DispatchRequest = DispatchRequest(),
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE"]))
):
    """
    Dispatches emergency vehicle to distress incident.
    If vehicle_id is omitted, automatically executes nearest-unit spatial matching.
    """
    try:
        return await sos_service.dispatch_vehicle(sos_id=sos_id, vehicle_id=req.vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{sos_id}/resolve")
async def resolve_distress_incident(
    sos_id: str,
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE", "FLEET_DRIVER"]))
):
    """Marks distress call as resolved and releases assigned rescue unit back to ready pool."""
    try:
        return await sos_service.resolve_sos(sos_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
