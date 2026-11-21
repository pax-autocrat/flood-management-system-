"""
JalRakshak NCR — Master 36 Drains & Desilting Operations Router (Phase 2)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.drain_service import drain_service
from routers.auth_router import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/drains", tags=["Stormwater Drains & Desilting"])

class DrainStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New drain state: CLOGGED, DESILTING_IN_PROGRESS, CLEANED, VERIFIED")

class DesiltingAuditLogRequest(BaseModel):
    contractor_name: str = Field(..., description="Contractor firm or direct crew name (e.g. 'Shree Ram Infra Ltd')")
    dredged_volume_m3: float = Field(..., description="Volume of silt removed in cubic meters (m³)", ge=1.0)
    photo_before_url: Optional[str] = Field(default=None, description="URL of pre-desilting photograph")
    photo_after_url: Optional[str] = Field(default=None, description="URL of post-desilting cleared catch basin")
    notes: Optional[str] = Field(default=None, description="Inspection observation notes")
    inspector_name: Optional[str] = Field(default="MCG Junior Engineer", description="Verifying municipal inspector")

@router.get("")
def list_master_drains(
    leg: Optional[str] = Query(None, description="Filter by corridor: 'LEG 1', 'LEG 2', 'LEG 3'"),
    status: Optional[str] = Query(None, description="Filter by status: 'CLOGGED', 'CLEANED', etc.")
):
    """Returns all 36 Gurugram master stormwater drains with live silt metrics."""
    drains = drain_service.get_all_drains(leg=leg, status=status)
    return {
        "count": len(drains),
        "total_master_drains": 36,
        "drains": drains
    }

@router.get("/summary")
def get_desilting_summary():
    """Returns city-wide desilting progress percentage and dredging volume totals."""
    return drain_service.get_drain_summary()

@router.get("/{drain_id}")
def get_drain_detail(drain_id: str):
    """Retrieves full drain profile and photographic inspection history."""
    drain = drain_service.get_drain_by_id(drain_id)
    if not drain:
        raise HTTPException(status_code=404, detail=f"Drain '{drain_id}' not found.")
    return drain

@router.patch("/{drain_id}/status")
def update_drain_status(
    drain_id: str,
    req: DrainStatusUpdateRequest,
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL"]))
):
    """Updates drain operational state. Gated strictly for officials."""
    valid_statuses = ("CLOGGED", "DESILTING_IN_PROGRESS", "CLEANED", "VERIFIED")
    if req.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}."
        )

    drain = drain_service.update_drain_status(drain_id, req.status)
    if not drain:
        raise HTTPException(status_code=404, detail=f"Drain '{drain_id}' not found.")
    return {
        "status": "updated",
        "drain": drain,
        "updated_by": current_official["name"]
    }

@router.post("/{drain_id}/audit")
def log_contractor_audit_proof(
    drain_id: str,
    req: DesiltingAuditLogRequest,
    current_official: Dict[str, Any] = Depends(require_roles(["MCG_OFFICIAL", "GMDA_OFFICIAL"]))
):
    """Logs tamper-evident desilting audit proof with before/after photo URLs and dredged silt volume."""
    try:
        audit_record = drain_service.log_desilting_audit(
            drain_id=drain_id,
            contractor_name=req.contractor_name,
            dredged_volume_m3=req.dredged_volume_m3,
            photo_before_url=req.photo_before_url,
            photo_after_url=req.photo_after_url,
            notes=req.notes,
            inspector_name=current_official.get("name") or req.inspector_name
        )
        return audit_record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
