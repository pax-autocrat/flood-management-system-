"""
JalRakshak NCR - Multi-Agency Coordination & Disaster Logistics Router
Endpoints for DHBVN power cut protocols, automated underpass boom barriers,
emergency relief shelters/MLCP dry parking sanctuaries, and official insurance claim certificate PDF generation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from services.agency_service import agency_service
from routers.auth_router import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/agency", tags=["Multi-Agency Disaster Coordination"])


# --- Pydantic Request Models ---
class DHBVNPowerCutRequest(BaseModel):
    feeder_id: str = Field(..., example="FDR-RJ-03")
    water_depth_cm: Optional[int] = Field(None, example=45)
    reason: Optional[str] = Field("Transformer footing submerged; shock prevention protocol triggered", example="Flooding near service lane")


class DHBVNExecuteRequest(BaseModel):
    feeder_id: str = Field(..., example="FDR-RJ-03")


class DHBVNRestoreRequest(BaseModel):
    feeder_id: str = Field(..., example="FDR-RJ-03")


class BarrierToggleRequest(BaseModel):
    state: str = Field(..., example="CLOSED")  # OPEN or CLOSED
    reason: Optional[str] = Field("Water level exceeded 35cm critical threshold; closing to prevent trapped motorists", example="Submerged underpass")


class InsuranceCertificateRequest(BaseModel):
    citizen_name: str = Field(..., example="Kamal Shukla")
    citizen_phone: str = Field(..., example="+91-9811223344")
    vehicle_registration: str = Field(..., example="HR-26-DK-9012")
    vehicle_make_model: str = Field(..., example="Honda City 1.5 i-VTEC (Sedan)")
    incident_location: str = Field(..., example="Rajiv Chowk Underpass South Exit (NH-48)")
    incident_date_time: Optional[str] = Field(None, example="20 July 2026, 17:30 HRS IST")
    flood_water_depth_cm: Optional[int] = Field(115, example=115)
    incident_description: Optional[str] = Field(
        "Vehicle engine hydro-locked and stalled due to flash flood runoff surcharging Rajiv Chowk underpass.",
        example="Hydrolock in deep water"
    )
    citizen_aadhaar_last4: Optional[str] = Field("4590", example="4590")
    hotspot_id: Optional[str] = Field("hs_rajiv", example="hs_rajiv")


# --- DHBVN Electrical Substation Endpoints ---
@router.get("/dhbvn/feeders")
def list_dhbvn_feeders():
    """
    Returns live operational status of 11kV electrical feeders across flood-prone zones.
    """
    return agency_service.get_dhbvn_feeders()


@router.post("/dhbvn/power-cut")
def request_dhbvn_power_cut(
    req: DHBVNPowerCutRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Request emergency power cut to prevent electrocution hazards at submerged substations.
    Authorized for DHBVN, MCG, GMDA, SDRF officials.
    """
    if current_user.get("role") == "CITIZEN":
        raise HTTPException(status_code=403, detail="Only municipal or grid control officials can trigger power cuts.")

    try:
        agency_name = current_user.get("agency_code") or "OFFICIAL"
        res = agency_service.request_dhbvn_power_cut(
            feeder_id=req.feeder_id,
            requested_by=f"{current_user.get('name')} ({agency_name})",
            water_depth_cm=req.water_depth_cm,
            reason=req.reason or ""
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/dhbvn/execute")
def execute_dhbvn_power_cut(
    req: DHBVNExecuteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Confirms physical electrical isolation of feeder line.
    Authorized for DHBVN Linemen / Substation Engineers.
    """
    if current_user.get("agency_code") != "DHBVN" and current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Only DHBVN engineers or Admin can execute power cuts.")

    try:
        res = agency_service.execute_dhbvn_power_cut(
            feeder_id=req.feeder_id,
            executed_by=f"{current_user.get('name')} (DHBVN)"
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/dhbvn/restore")
def restore_dhbvn_power(
    req: DHBVNRestoreRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Re-energizes the feeder line after water recedes and safety check completes.
    """
    if current_user.get("agency_code") != "DHBVN" and current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Only DHBVN engineers or Admin can re-energize lines.")

    try:
        res = agency_service.restore_dhbvn_power(
            feeder_id=req.feeder_id,
            restored_by=f"{current_user.get('name')} (DHBVN)"
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Underpass Automated Boom Barriers Endpoints ---
@router.get("/barriers")
def list_boom_barriers():
    """
    Lists status and hydrological triggers for all underpass boom barriers in Gurugram.
    """
    return agency_service.get_underpass_barriers()


@router.post("/barriers/{barrier_id}/toggle")
def toggle_boom_barrier(
    barrier_id: str,
    req: BarrierToggleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Remotely lowers or raises an underpass automated boom barrier.
    Restricted to Traffic Police, MCG, GMDA, NHAI officials.
    """
    if current_user.get("role") == "CITIZEN":
        raise HTTPException(status_code=403, detail="Only authorized traffic or municipal personnel can operate boom barriers.")

    try:
        agency_name = current_user.get("agency_code") or "OFFICIAL"
        res = agency_service.toggle_boom_barrier(
            barrier_id=barrier_id,
            new_state=req.state,
            operator_name=f"{current_user.get('name')} ({agency_name})",
            reason=req.reason or ""
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Emergency Relief Shelters & MLCP Parking Sanctuaries ---
@router.get("/shelters")
def list_emergency_shelters(
    shelter_type: Optional[str] = Query(None, description="RELIEF_CAMP, MLCP_PARKING, COMMUNITY_CENTER, GOVT_SCHOOL"),
    lat: Optional[float] = Query(None, description="User latitude for nearest distance sorting"),
    lng: Optional[float] = Query(None, description="User longitude for nearest distance sorting"),
    radius_km: float = Query(25.0, description="Max search radius in kilometers")
):
    """
    Citizen-facing & Official directory of safe dry parking garages (MLCP) and emergency shelters with supplies.
    """
    return agency_service.get_emergency_shelters(
        shelter_type=shelter_type,
        user_lat=lat,
        user_lng=lng,
        radius_km=radius_km
    )


# --- Official Flood Incident Certificate Generator (PDF) ---
@router.post("/insurance-certificate")
def generate_flood_certificate(req: InsuranceCertificateRequest):
    """
    Generates an official, tamper-evident PDF verification certificate
    issued under Section 34 of the Disaster Management Act, 2005
    for insurance companies to process Act-of-God flood damage claims.
    """
    try:
        pdf_bytes = agency_service.generate_insurance_certificate(
            citizen_name=req.citizen_name,
            citizen_phone=req.citizen_phone,
            vehicle_registration=req.vehicle_registration,
            vehicle_make_model=req.vehicle_make_model,
            incident_location=req.incident_location,
            incident_date_time=req.incident_date_time,
            flood_water_depth_cm=req.flood_water_depth_cm or 85,
            incident_description=req.incident_description or "",
            citizen_aadhaar_last4=req.citizen_aadhaar_last4 or "XXXX",
            hotspot_id=req.hotspot_id
        )

        safe_filename = req.vehicle_registration.replace(" ", "_").replace("-", "_")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=MCG_Flood_Certificate_{safe_filename}.pdf",
                "X-Certificate-Type": "Act-Of-God-Disaster-Verification"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate certificate PDF: {str(e)}")
