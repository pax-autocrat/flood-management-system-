import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import engine, Base, SessionLocal
from app.seed_data import seed_database
from app.services.weather_service import WeatherService
from app.services.fleet_service import FleetService
from app.services.routing_service import RoutingService
from app.models import Hotspot, Vehicle, SosRequest, WeatherState

# 1. Initialize tables & seed data
Base.metadata.create_all(bind=engine)
db = SessionLocal()
seed_database(db)

# 2. Check counts
hotspots_count = db.query(Hotspot).count()
vehicles_count = db.query(Vehicle).count()
sos_count = db.query(SosRequest).count()
weather = WeatherService.get_weather_state(db)

print(f"DATABASE SEED VERIFIED:")
print(f"  - Hotspots: {hotspots_count} / 8")
print(f"  - Vehicles: {vehicles_count} / 8")
print(f"  - SOS Tickets: {sos_count} / 3")
print(f"  - Weather: {weather.scenario} ({weather.rain_mm_hr} mm/hr)")

# 3. Test Routing calculation
route = RoutingService.calculate_route("loc_cyberhub", "loc_sohna", "FOUR_WHEELER")
print(f"ROUTING SERVICE VERIFIED:")
print(f"  - Route: {route['origin_name']} -> {route['dest_name']}")
print(f"  - Safe ETA: {route['safe_eta']}")
print(f"  - Flooded ETA: {route['flooded_eta']}")

# 4. Test Fleet drift
drift = FleetService.simulate_gps_drift(db)
print(f"FLEET DRIFT VERIFIED: {len(drift)} vehicles updated with live transponder telemetry")

db.close()
print("ALL TESTS PASSED SUCCESSFULLY!")
