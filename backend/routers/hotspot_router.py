"""
JalRakshak NCR — Persistent Hotspot Telemetry Router (Phase 2)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.hotspot_service import hotspot_service
from routers.auth_router import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/hotspots", tags=["Hotspots & Telemetry"])

class TelemetryUpdateRequest(BaseModel):
    depth_cm: int = Field(..., description="Measured water depth in cm", ge=0, le=300)

class ToggleActionRequest(BaseModel):
    active: Optional[bool] = Field(default=None, description="Explicit state boolean, or None to flip")

@router.get("")
def list_hotspots(weather_factor: float = Query(1.0, description="Weather rain multiplier (0.18 normal, 0.52 ai, 1.0 storm)")):
    """Returns all persistent hotspots with effective water depths and passability."""
    hotspots = hotspot_service.get_all_hotspots(weather_factor)
    return {
        "count": len(hotspots),
        "weather_factor": weather_factor,
        "hotspots": hotspots
    }

@router.get("/road-safety")
def get_road_safety_percentage(weather_factor: float = Query(1.0, description="Weather rain multiplier")):
    """Calculates official MCG Road Safety Percentage metric."""
    return hotspot_service.get_road_safety_metrics(weather_factor)

@router.get("/{spot_id}")
def get_hotspot_detail(spot_id: str, weather_factor: float = Query(1.0)):
    """Lookup a single persistent hotspot by ID or Code."""
    spot = hotspot_service.get_hotspot_by_id(spot_id, weather_factor)
    if not spot:
        raise HTTPException(status_code=404, detail=f"Hotspot '{spot_id}' not found.")
    return spot

@router.patch("/{spot_id}/telemetry")
def update_hotspot_telemetry(
    spot_id: str,
    req: TelemetryUpdateRequest,
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL", "SDRF_RESCUE"]))
):
    """Updates water level sensor telemetry. Strictly official-only."""
    spot = hotspot_service.update_telemetry(spot_id, req.depth_cm)
    if not spot:
        raise HTTPException(status_code=404, detail=f"Hotspot '{spot_id}' not found.")
    return {
        "status": "updated",
        "hotspot": spot,
        "updated_by": current_official["name"]
    }

@router.post("/{spot_id}/toggle-pump")
def toggle_pump_status(
    spot_id: str,
    req: ToggleActionRequest = ToggleActionRequest(),
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL"]))
):
    """Assigns or releases high-capacity submersible dewatering pump at hotspot."""
    spot = hotspot_service.toggle_pump(spot_id, req.active)
    if not spot:
        raise HTTPException(status_code=404, detail=f"Hotspot '{spot_id}' not found.")
    return {
        "status": "pump_state_changed",
        "pump_assigned": bool(spot["pump_assigned"]),
        "effective_depth_cm": spot["effective_depth_cm"],
        "hotspot": spot
    }

@router.post("/{spot_id}/toggle-drain")
def toggle_drain_status(
    spot_id: str,
    req: ToggleActionRequest = ToggleActionRequest(),
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL"]))
):
    """Marks stormwater drain as Cleaned or Clogged (Cleaned grants 40% water depth reduction)."""
    spot = hotspot_service.toggle_drain(spot_id, req.active)
    if not spot:
        raise HTTPException(status_code=404, detail=f"Hotspot '{spot_id}' not found.")
    return {
        "status": "drain_state_changed",
        "drain_cleaned": bool(spot["drain_cleaned"]),
        "effective_depth_cm": spot["effective_depth_cm"],
        "hotspot": spot
    }
