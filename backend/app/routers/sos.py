import random
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SosRequest, Vehicle, Hotspot
from app.schemas import SosResponse, SosRequestCreate, SosAssignRequest

router = APIRouter(prefix="/sos", tags=["SOS Distress Queue"])

@router.get("", response_model=List[SosResponse])
def get_sos_requests(db: Session = Depends(get_db)):
    return db.query(SosRequest).order_by(SosRequest.id.desc()).all()

@router.post("", response_model=SosResponse)
def create_sos_request(payload: SosRequestCreate, db: Session = Depends(get_db)):
    # Generate unique ID
    new_id = f"SOS-{random.randint(104, 999)}"
    while db.query(SosRequest).filter(SosRequest.id == new_id).first():
        new_id = f"SOS-{random.randint(104, 999)}"

    # Determine coordinates
    lat = payload.lat
    lng = payload.lng
    if lat is None or lng is None:
        if payload.spot_id:
            spot = db.query(Hotspot).filter(Hotspot.id == payload.spot_id).first()
            if spot:
                lat = round(spot.lat + (random.random() - 0.5) * 0.002, 4)
                lng = round(spot.lng + (random.random() - 0.5) * 0.002, 4)
        if lat is None or lng is None:
            lat = 28.4456
            lng = 77.0339

    sos = SosRequest(
        id=new_id,
        person=payload.person,
        spot_id=payload.spot_id,
        location=payload.location,
        issue=payload.issue,
        note=payload.note,
        time_reported="Just now",
        lat=lat,
        lng=lng,
        assigned_truck=None,
        status="PENDING"
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)
    return sos

@router.post("/{sos_id}/assign", response_model=SosResponse)
def assign_vehicle_to_sos(sos_id: str, payload: Optional[SosAssignRequest] = None, db: Session = Depends(get_db)):
    sos = db.query(SosRequest).filter(SosRequest.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found")

    truck = None
    if payload and payload.vehicle_id:
        truck = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    else:
        # Auto-pick first OPEN vehicle
        truck = db.query(Vehicle).filter(Vehicle.status == "OPEN").first()

    if not truck:
        raise HTTPException(status_code=400, detail="No emergency vehicle available to assign")

    truck.status = "OCCUPIED"
    truck.route = f"Responding to {sos.location} ({sos.id})"
    sos.assigned_truck = truck.id
    sos.status = "ASSIGNED"
    db.commit()
    db.refresh(sos)
    return sos

@router.delete("/{sos_id}")
def resolve_sos_request(sos_id: str, db: Session = Depends(get_db)):
    sos = db.query(SosRequest).filter(SosRequest.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS request not found")
    db.delete(sos)
    db.commit()
    return {"message": f"SOS {sos_id} marked as resolved"}
