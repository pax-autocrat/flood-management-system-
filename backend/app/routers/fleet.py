import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Vehicle
from app.schemas import VehicleResponse, VehicleStatusUpdate, VehicleDispatchRequest
from app.services.fleet_service import FleetService

router = APIRouter(prefix="/fleet", tags=["Emergency Vehicle Fleet"])

@router.get("", response_model=List[VehicleResponse])
def get_all_vehicles(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return FleetService.get_vehicles(db, status=status, category=category)

@router.get("/positions/drift")
def simulate_gps_drift(db: Session = Depends(get_db)):
    """Simulates real-time GPS drift for all 8 vehicles and returns updated positions."""
    return FleetService.simulate_gps_drift(db)

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle_by_id(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
def update_vehicle_status(vehicle_id: str, payload: VehicleStatusUpdate, db: Session = Depends(get_db)):
    vehicle = FleetService.update_vehicle_status(db, vehicle_id, payload.status)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.post("/{vehicle_id}/dispatch", response_model=VehicleResponse)
def dispatch_vehicle(vehicle_id: str, payload: VehicleDispatchRequest, db: Session = Depends(get_db)):
    vehicle = FleetService.dispatch_vehicle(
        db,
        vehicle_id=vehicle_id,
        target_spot_id=payload.target_spot_id,
        target_sos_id=payload.target_sos_id,
        lat=payload.lat,
        lng=payload.lng,
        note=payload.note
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.websocket("/ws/live-gps")
async def websocket_live_gps(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                positions = FleetService.simulate_gps_drift(db)
                await websocket.send_json({"type": "FLEET_GPS_UPDATE", "vehicles": positions})
            finally:
                db.close()
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
