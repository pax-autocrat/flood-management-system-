"""
JalRakshak NCR — Crowdsourced "Jal-Doot" & Hazard Router (Phase 5)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from services.crowdsource_service import crowdsource_service

router = APIRouter(prefix="/api/v1/reports", tags=["Crowdsourcing & Jal-Doot"])

class CrowdsourceReportRequest(BaseModel):
    reporter_name: str = Field(..., description="Name of reporting commuter or citizen")
    reporter_phone: str = Field(..., description="Contact phone number")
    location_address: str = Field(..., description="Sector, colony, or road name")
    lat: float = Field(..., description="GPS Latitude")
    lng: float = Field(..., description="GPS Longitude")
    estimated_depth_cm: int = Field(default=30, ge=5, le=250, description="Estimated water depth in cm")
    is_manhole_open: bool = Field(default=False, description="Flag for deadly open manhole hazard")
    is_wire_hazard: bool = Field(default=False, description="Flag for fallen live wire / submerged transformer")
    is_submerged_vehicle: bool = Field(default=False, description="Flag for floating or stranded car")
    photo_url: Optional[str] = Field(default=None, description="URL of uploaded photograph")
    has_exif_gps: bool = Field(default=False, description="Whether GPS was auto-extracted from photo EXIF")
    ai_confidence_score: float = Field(default=0.88, ge=0.0, le=1.0, description="Computer vision confidence score")

class CommunityVoteRequest(BaseModel):
    vote_type: str = Field(..., description="Vote action: 'STILL_FLOODED' (upvote) or 'WATER_RECEDED' (downvote)")

@router.post("")
async def submit_waterlogging_report(req: CrowdsourceReportRequest):
    """
    Submits crowdsourced waterlogging / hazard report.
    Instantly pins report on civic map with 4-hour automatic TTL expiry.
    """
    created = await crowdsource_service.create_crowdsourced_report(
        reporter_name=req.reporter_name,
        reporter_phone=req.reporter_phone,
        lat=req.lat,
        lng=req.lng,
        location_address=req.location_address,
        estimated_depth_cm=req.estimated_depth_cm,
        is_manhole_open=req.is_manhole_open,
        is_wire_hazard=req.is_wire_hazard,
        is_submerged_vehicle=req.is_submerged_vehicle,
        photo_url=req.photo_url or "https://s3.jalrakshak.in/reports/default.jpg",
        has_exif_gps=req.has_exif_gps,
        ai_confidence_score=req.ai_confidence_score
    )
    return {
        "status": "report_published",
        "report_id": created["id"],
        "ai_verification_badge": created["status"],
        "expires_at": created["expires_at"],
        "report": created
    }

@router.get("")
def list_active_community_reports(
    user_lat: Optional[float] = Query(None, description="Current user Latitude for radius filtering"),
    user_lng: Optional[float] = Query(None, description="Current user Longitude for radius filtering"),
    radius_km: Optional[float] = Query(None, description="Radius filter in kilometers (e.g. 3.0 km)"),
    hazard_only: bool = Query(False, description="Show only life-threatening hazards (open manholes / live wires)")
):
    """Returns active unexpired crowdsourced pins, with optional spatial proximity filtering."""
    reports = crowdsource_service.get_active_reports(
        user_lat=user_lat,
        user_lng=user_lng,
        radius_km=radius_km,
        hazard_only=hazard_only
    )
    return {
        "count": len(reports),
        "reports": reports
    }

@router.get("/{report_id}")
def get_report_detail(report_id: str):
    """Lookup community hazard report by ID."""
    rep = crowdsource_service.get_report_by_id(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return rep

@router.post("/{report_id}/vote")
def cast_community_verification_vote(report_id: str, req: CommunityVoteRequest):
    """
    Community 'Still Flooded?' verification vote.
    Upvotes extend TTL and award 'CONFIRMED_COMMUNITY' badge; downvotes mark hazard as CLEARED.
    """
    try:
        updated = crowdsource_service.vote_on_report(report_id, req.vote_type)
        return {
            "status": "vote_recorded",
            "report_id": report_id,
            "new_status": updated["status"],
            "upvotes": updated["upvotes"],
            "downvotes": updated["downvotes"]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
