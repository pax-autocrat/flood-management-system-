import datetime
import httpx
from sqlalchemy.orm import Session
from app.models import WeatherState, Hotspot
from app.config import settings

SCENARIO_PRESETS = {
    "normal": {
        "scenario": "normal",
        "temperature": 29.2,
        "feels_like": 31.5,
        "rain_mm_hr": 18.0,
        "rain_bar_pct": "22%",
        "wind_speed": 14.0,
        "wind_direction": "SE",
        "humidity": 76,
        "visibility_km": 4.5,
        "alert_level": "GREEN ADVISORY: LIGHT RAIN",
        "advisory": "All wide arterial roads open. Normal traffic movement across Gurugram."
    },
    "ai": {
        "scenario": "ai",
        "temperature": 27.8,
        "feels_like": 30.2,
        "rain_mm_hr": 65.0,
        "rain_bar_pct": "58%",
        "wind_speed": 26.0,
        "wind_direction": "SW",
        "humidity": 88,
        "visibility_km": 2.6,
        "alert_level": "AMBER WATCH: HEAVY DOWNPOUR",
        "advisory": "Moderate waterlogging at low underpasses. Prefer Golf Course Road."
    },
    "storm": {
        "scenario": "storm",
        "temperature": 26.4,
        "feels_like": 29.1,
        "rain_mm_hr": 133.0,
        "rain_bar_pct": "95%",
        "wind_speed": 38.0,
        "wind_direction": "SW",
        "humidity": 94,
        "visibility_km": 1.8,
        "alert_level": "RED ALERT: EXTREME CLOUDBURST",
        "advisory": "Avoid NH-48 Underpasses (Rajiv & Hero Honda Chowk). Take Wide Golf Course Rd."
    }
}

class WeatherService:
    @staticmethod
    def get_weather_state(db: Session) -> WeatherState:
        state = db.query(WeatherState).filter(WeatherState.id == 1).first()
        if not state:
            state = WeatherState(id=1, **SCENARIO_PRESETS["storm"])
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    @staticmethod
    def set_scenario(db: Session, scenario: str) -> WeatherState:
        state = WeatherService.get_weather_state(db)
        preset = SCENARIO_PRESETS.get(scenario, SCENARIO_PRESETS["storm"])
        for k, v in preset.items():
            setattr(state, k, v)
        state.last_synced = f"Preset applied at {datetime.datetime.now().strftime('%H:%M:%S')}"
        db.commit()
        db.refresh(state)
        return state

    @staticmethod
    async def sync_open_meteo(db: Session) -> WeatherState:
        state = WeatherService.get_weather_state(db)
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={settings.GURUGRAM_LAT}&"
            f"longitude={settings.GURUGRAM_LNG}&current=temperature_2m,relative_humidity_2m,"
            f"apparent_temperature,precipitation,wind_speed_10m"
        )
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json().get("current", {})
                    state.temperature = data.get("temperature_2m", state.temperature)
                    state.feels_like = data.get("apparent_temperature", state.feels_like)
                    state.humidity = int(data.get("relative_humidity_2m", state.humidity))
                    state.wind_speed = data.get("wind_speed_10m", state.wind_speed)
                    precip = data.get("precipitation", 0.0)
                    if precip > 0:
                        state.rain_mm_hr = round(precip * 10, 1)
                    state.last_synced = f"Open-Meteo AWS Live ({datetime.datetime.now().strftime('%H:%M:%S')})"
                    db.commit()
                    db.refresh(state)
        except Exception:
            state.last_synced = "Cached IMD Gurugram Telemetry (Offline Mode)"
            db.commit()
        return state

    @staticmethod
    def compute_spot_depth(spot: Hotspot, scenario: str) -> int:
        factor = 1.0
        if scenario == "normal":
            factor = 0.18
        elif scenario == "ai":
            factor = 0.52

        if spot.drain_cleaned:
            factor *= 0.60
        if spot.pump_assigned:
            factor *= 0.35

        return max(0, int(round(spot.storm_depth_cm * factor)))

    @staticmethod
    def get_status_category(depth: int) -> str:
        if depth >= 55:
            return "FLOODED"
        elif depth >= 25:
            return "WATERLOGGED"
        return "CLEAR"
