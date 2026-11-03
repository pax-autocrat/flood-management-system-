from sqlalchemy import Column, String, Integer, Float, Boolean
from app.database import Base

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(String, primary_key=True, index=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    area = Column(String, nullable=False)
    bypass = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    road_width = Column(String, default="Wide 6-Lane")
    drain_cleaned = Column(Boolean, default=False)
    cleaner_team = Column(String, default="Cleaner Unit")
    storm_depth_cm = Column(Integer, default=100)
    pump_assigned = Column(Boolean, default=False)

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # TANKER | AMBULANCE | BOAT | QRV
    category_label = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    driver = Column(String, nullable=False)
    route = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String, default="OPEN")  # OPEN | OCCUPIED

class SosRequest(Base):
    __tablename__ = "sos_requests"

    id = Column(String, primary_key=True, index=True)
    person = Column(String, nullable=False)
    spot_id = Column(String, nullable=True)
    location = Column(String, nullable=False)
    issue = Column(String, nullable=False)
    note = Column(String, nullable=False)
    time_reported = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    assigned_truck = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING | ASSIGNED | RESOLVED

class WeatherState(Base):
    __tablename__ = "weather_state"

    id = Column(Integer, primary_key=True)
    scenario = Column(String, default="storm")  # normal | ai | storm
    temperature = Column(Float, default=26.4)
    feels_like = Column(Float, default=29.1)
    rain_mm_hr = Column(Float, default=133.0)
    rain_bar_pct = Column(String, default="95%")
    wind_speed = Column(Float, default=38.0)
    wind_direction = Column(String, default="SW")
    humidity = Column(Integer, default=94)
    visibility_km = Column(Float, default=1.8)
    alert_level = Column(String, default="RED ALERT: EXTREME CLOUDBURST")
    advisory = Column(String, default="Avoid NH-48 Underpasses (Rajiv & Hero Honda Chowk). Take Wide Golf Course Rd.")
    last_synced = Column(String, default="")
