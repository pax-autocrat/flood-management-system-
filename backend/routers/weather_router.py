"""
JalRakshak NCR — Live Weather & Radar Telemetry Router (Phase 2)
Engineered for Team NeerNetra (SustainX 2026)
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from services.weather_engine import weather_engine

router = APIRouter(prefix="/api/v1/weather", tags=["Live Weather & Hydrology"])

class ScenarioChangeRequest(BaseModel):
    scenario: str = Field(..., description="Weather preset: 'normal' (18mm/hr), 'ai' (65mm/hr), 'storm' (133mm/hr)")

@router.get("/current")
def get_current_weather():
    """Returns active Gurugram IMD Automatic Weather Station (AWS) telemetry."""
    return weather_engine.get_current_weather()

@router.post("/scenario")
def set_weather_scenario(req: ScenarioChangeRequest):
    """Switches calibrated weather scenario preset and updates city flood multiplier."""
    try:
        return weather_engine.set_scenario(req.scenario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/sync-api")
async def sync_live_open_meteo():
    """Polls real Open-Meteo API for Gurugram coordinates and synchronizes live telemetry."""
    return await weather_engine.sync_live_open_meteo()

@router.get("/accumulation")
def get_24h_rainfall_accumulation():
    """Returns 24-hour hourly rainfall accumulation curve and flood load metrics."""
    return weather_engine.get_24h_accumulation_curve()

@router.get("/radar")
def get_doppler_radar_reflectivity():
    """Returns IMD Doppler weather radar reflectivity loop metadata over Gurugram/NCR."""
    return weather_engine.get_radar_reflectivity_loop()
