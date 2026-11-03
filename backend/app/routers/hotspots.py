from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Hotspot, Vehicle, SosRequest
from app.schemas import HotspotResponse, HotspotDrainUpdate, DashboardKpiResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/hotspots", tags=["Flood Hotspots & Desilting"])

def build_hotspot_response(spot: Hotspot, scenario: str) -> HotspotResponse:
    depth = WeatherService.compute_spot_depth(spot, scenario)
    category = WeatherService.get_status_category(depth)
    return HotspotResponse(
        id=spot.id,
        code=spot.code,
        name=spot.name,
        area=spot.area,
        bypass=spot.bypass,
        lat=spot.lat,
        lng=spot.lng,
        road_width=spot.road_width,
        drain_cleaned=spot.drain_cleaned,
        cleaner_team=spot.cleaner_team,
        storm_depth_cm=spot.storm_depth_cm,
        pump_assigned=spot.pump_assigned,
        current_depth_cm=depth,
        status_category=category
    )

@router.get("", response_model=List[HotspotResponse])
def get_all_hotspots(db: Session = Depends(get_db)):
    weather_state = WeatherService.get_weather_state(db)
    spots = db.query(Hotspot).all()
    return [build_hotspot_response(s, weather_state.scenario) for s in spots]

@router.get("/kpis/summary", response_model=DashboardKpiResponse)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    weather_state = WeatherService.get_weather_state(db)
    spots = db.query(Hotspot).all()

    safe_count = 0
    watch_count = 0
    flood_count = 0

    for s in spots:
        d = WeatherService.compute_spot_depth(s, weather_state.scenario)
        if d < 25:
            safe_count += 1
        elif d < 55:
            watch_count += 1
        else:
            flood_count += 1

    total_spots = len(spots) or 1
    road_safety_pct = int(round(((safe_count + watch_count * 0.5) / total_spots) * 100))

    cleaned_spots_count = sum(1 for s in spots if s.drain_cleaned)
    total_cleaned_drains = 14 + cleaned_spots_count
    desilted_pct = int(round((total_cleaned_drains / 36) * 100))

    active_sos = db.query(SosRequest).count()
    open_vehicles = db.query(Vehicle).filter(Vehicle.status == "OPEN").count()
    total_vehicles = db.query(Vehicle).count()

    return DashboardKpiResponse(
        road_safety_pct=road_safety_pct,
        desilted_ratio=f"{total_cleaned_drains} / 36",
        desilted_pct=desilted_pct,
        active_sos_count=active_sos,
        open_vehicles_count=open_vehicles,
        total_vehicles_count=total_vehicles,
        safe_spots_count=safe_count,
        watch_spots_count=watch_count,
        flooded_spots_count=flood_count
    )

@router.get("/{spot_id}", response_model=HotspotResponse)
def get_hotspot_by_id(spot_id: str, db: Session = Depends(get_db)):
    weather_state = WeatherService.get_weather_state(db)
    spot = db.query(Hotspot).filter(Hotspot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    return build_hotspot_response(spot, weather_state.scenario)

@router.patch("/{spot_id}/drain", response_model=HotspotResponse)
def update_hotspot_drain_status(spot_id: str, payload: HotspotDrainUpdate, db: Session = Depends(get_db)):
    spot = db.query(Hotspot).filter(Hotspot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    spot.drain_cleaned = payload.drain_cleaned
    db.commit()
    db.refresh(spot)
    weather_state = WeatherService.get_weather_state(db)
    return build_hotspot_response(spot, weather_state.scenario)
