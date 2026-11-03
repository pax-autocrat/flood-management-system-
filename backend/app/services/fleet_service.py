import random
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import Vehicle, Hotspot, SosRequest

class FleetService:
    @staticmethod
    def get_vehicles(
        db: Session,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Vehicle]:
        query = db.query(Vehicle)
        if status and status != "ALL":
            query = query.filter(Vehicle.status == status)
        if category and category != "ALL":
            query = query.filter(Vehicle.category == category)
        return query.all()

    @staticmethod
    def update_vehicle_status(db: Session, vehicle_id: str, new_status: str) -> Optional[Vehicle]:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if vehicle:
            vehicle.status = new_status
            db.commit()
            db.refresh(vehicle)
        return vehicle

    @staticmethod
    def dispatch_vehicle(
        db: Session,
        vehicle_id: str,
        target_spot_id: Optional[str] = None,
        target_sos_id: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        note: Optional[str] = None
    ) -> Optional[Vehicle]:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            return None

        vehicle.status = "OCCUPIED"

        if target_spot_id:
            spot = db.query(Hotspot).filter(Hotspot.id == target_spot_id).first()
            if spot:
                vehicle.lat = spot.lat
                vehicle.lng = spot.lng
                vehicle.route = f"Pumping at {spot.name}"
                spot.pump_assigned = True
                db.commit()

        elif target_sos_id:
            sos = db.query(SosRequest).filter(SosRequest.id == target_sos_id).first()
            if sos:
                vehicle.lat = sos.lat
                vehicle.lng = sos.lng
                vehicle.route = f"Responding to {sos.location} ({sos.id})"
                sos.assigned_truck = vehicle.id
                sos.status = "ASSIGNED"
                db.commit()

        elif lat is not None and lng is not None:
            vehicle.lat = lat
            vehicle.lng = lng
            vehicle.route = note or "Dispatched to incident"
            db.commit()

        db.refresh(vehicle)
        return vehicle

    @staticmethod
    def simulate_gps_drift(db: Session) -> List[dict]:
        """Simulates slight movement for all vehicles (live GPS transponder feed)."""
        vehicles = db.query(Vehicle).all()
        positions = []
        for v in vehicles:
            drift_lat = (random.random() - 0.5) * 0.0004
            drift_lng = (random.random() - 0.5) * 0.0004
            v.lat = round(v.lat + drift_lat, 4)
            v.lng = round(v.lng + drift_lng, 4)
            positions.append({
                "id": v.id,
                "name": v.name,
                "category": v.category,
                "status": v.status,
                "lat": v.lat,
                "lng": v.lng,
                "route": v.route
            })
        db.commit()
        return positions
