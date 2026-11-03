from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import WeatherTelemetryResponse, WeatherScenarioUpdate
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather Telemetry"])

@router.get("/live", response_model=WeatherTelemetryResponse)
def get_live_weather(db: Session = Depends(get_db)):
    state = WeatherService.get_weather_state(db)
    return WeatherTelemetryResponse(
        scenario=state.scenario,
        temperature=state.temperature,
        feels_like=state.feels_like,
        rain_mm_hr=state.rain_mm_hr,
        rain_bar_pct=state.rain_bar_pct,
        wind_speed=state.wind_speed,
        wind_direction=state.wind_direction,
        humidity=state.humidity,
        visibility_km=state.visibility_km,
        alert_level=state.alert_level,
        advisory=state.advisory,
        last_synced=state.last_synced
    )

@router.post("/scenario", response_model=WeatherTelemetryResponse)
def update_weather_scenario(payload: WeatherScenarioUpdate, db: Session = Depends(get_db)):
    state = WeatherService.set_scenario(db, payload.scenario)
    return WeatherTelemetryResponse(
        scenario=state.scenario,
        temperature=state.temperature,
        feels_like=state.feels_like,
        rain_mm_hr=state.rain_mm_hr,
        rain_bar_pct=state.rain_bar_pct,
        wind_speed=state.wind_speed,
        wind_direction=state.wind_direction,
        humidity=state.humidity,
        visibility_km=state.visibility_km,
        alert_level=state.alert_level,
        advisory=state.advisory,
        last_synced=state.last_synced
    )

@router.post("/sync", response_model=WeatherTelemetryResponse)
async def sync_live_weather_api(db: Session = Depends(get_db)):
    state = await WeatherService.sync_open_meteo(db)
    return WeatherTelemetryResponse(
        scenario=state.scenario,
        temperature=state.temperature,
        feels_like=state.feels_like,
        rain_mm_hr=state.rain_mm_hr,
        rain_bar_pct=state.rain_bar_pct,
        wind_speed=state.wind_speed,
        wind_direction=state.wind_direction,
        humidity=state.humidity,
        visibility_km=state.visibility_km,
        alert_level=state.alert_level,
        advisory=state.advisory,
        last_synced=state.last_synced
    )
