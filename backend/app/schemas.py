from typing import Optional, List
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Auth Schemas
# -----------------------------------------------------------------------------
class LoginRequest(BaseModel):
    name: str
    passcode: str
    role: str = "OFFICIAL"  # OFFICIAL | CITIZEN

class LoginResponse(BaseModel):
    name: str
    role: str
    message: str
    token: str

# -----------------------------------------------------------------------------
# Weather Schemas
# -----------------------------------------------------------------------------
class WeatherTelemetryResponse(BaseModel):
    scenario: str
    temperature: float
    feels_like: float
    rain_mm_hr: float
    rain_bar_pct: str
    wind_speed: float
    wind_direction: str
    humidity: int
    visibility_km: float
    alert_level: str
    advisory: str
    last_synced: str

class WeatherScenarioUpdate(BaseModel):
    scenario: str = Field(..., pattern="^(normal|ai|storm)$")

# -----------------------------------------------------------------------------
# Hotspot Schemas
# -----------------------------------------------------------------------------
class HotspotResponse(BaseModel):
    id: str
    code: str
    name: str
    area: str
    bypass: str
    lat: float
    lng: float
    road_width: str
    drain_cleaned: bool
    cleaner_team: str
    storm_depth_cm: int
    pump_assigned: bool
    current_depth_cm: int
    status_category: str  # CLEAR | WATERLOGGED | FLOODED

class HotspotDrainUpdate(BaseModel):
    drain_cleaned: bool

# -----------------------------------------------------------------------------
# Vehicle Schemas
# -----------------------------------------------------------------------------
class VehicleResponse(BaseModel):
    id: str
    name: str
    category: str
    category_label: str
    icon: str
    driver: str
    route: str
    lat: float
    lng: float
    status: str  # OPEN | OCCUPIED

class VehicleStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|OCCUPIED)$")

class VehicleDispatchRequest(BaseModel):
    target_spot_id: Optional[str] = None
    target_sos_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    note: Optional[str] = None

# -----------------------------------------------------------------------------
# SOS Schemas
# -----------------------------------------------------------------------------
class SosRequestCreate(BaseModel):
    person: str
    spot_id: Optional[str] = None
    location: str
    issue: str
    note: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class SosResponse(BaseModel):
    id: str
    person: str
    spot_id: Optional[str]
    location: str
    issue: str
    note: str
    time_reported: str
    lat: float
    lng: float
    assigned_truck: Optional[str]
    status: str

class SosAssignRequest(BaseModel):
    vehicle_id: Optional[str] = None  # If none, auto-assigns first open vehicle

# -----------------------------------------------------------------------------
# Route Schemas
# -----------------------------------------------------------------------------
class RouteRequest(BaseModel):
    origin_key: str
    dest_key: str
    travel_mode: str = "FOUR_WHEELER"  # FOUR_WHEELER | TWO_WHEELER | ON_FOOT

class RoutePoint(BaseModel):
    lat: float
    lng: float

class RouteStep(BaseModel):
    time: str
    title: str
    sub: str

class RouteResponse(BaseModel):
    origin_name: str
    dest_name: str
    travel_mode: str
    safe_eta: str
    flooded_eta: str
    safe_waypoints: List[List[float]]
    flooded_waypoints: List[List[float]]
    steps: List[RouteStep]

# -----------------------------------------------------------------------------
# Summary Dashboard KPI Schema
# -----------------------------------------------------------------------------
class DashboardKpiResponse(BaseModel):
    road_safety_pct: int
    desilted_ratio: str
    desilted_pct: int
    active_sos_count: int
    open_vehicles_count: int
    total_vehicles_count: int
    safe_spots_count: int
    watch_spots_count: int
    flooded_spots_count: int
