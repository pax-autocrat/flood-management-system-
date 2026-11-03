from sqlalchemy.orm import Session
from app.models import Hotspot, Vehicle, SosRequest, WeatherState

INITIAL_HOTSPOTS = [
    {
        "id": "hs_rajiv",
        "code": "GRG-101",
        "name": "Rajiv Chowk Underpass",
        "area": "NH-48 → Sohna Road",
        "bypass": "Golf Course Rd → SPR",
        "lat": 28.4449,
        "lng": 77.0345,
        "road_width": "Wide 6-Lane",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-01",
        "storm_depth_cm": 115,
        "pump_assigned": False
    },
    {
        "id": "hs_herohonda",
        "code": "GRG-102",
        "name": "Hero Honda Chowk",
        "area": "NH-48 → Sector 34/37",
        "bypass": "SPR Wide Highway",
        "lat": 28.4265,
        "lng": 77.0031,
        "road_width": "Wide 6-Lane",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-02",
        "storm_depth_cm": 135,
        "pump_assigned": False
    },
    {
        "id": "hs_medanta",
        "code": "GRG-103",
        "name": "Medanta Hospital Road",
        "area": "Sector 38 → Subhash Chowk",
        "bypass": "Huda City Centre Wide Rd",
        "lat": 28.4394,
        "lng": 77.0416,
        "road_width": "4-Lane Road",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-03",
        "storm_depth_cm": 90,
        "pump_assigned": False
    },
    {
        "id": "hs_iffco",
        "code": "GRG-104",
        "name": "IFFCO Chowk Metro",
        "area": "MG Road → Cyber Hub",
        "bypass": "MG Road Elevated Corridor",
        "lat": 28.4773,
        "lng": 77.0689,
        "road_width": "Wide 6-Lane",
        "drain_cleaned": True,
        "cleaner_team": "Cleaner Unit #D-04",
        "storm_depth_cm": 35,
        "pump_assigned": True
    },
    {
        "id": "hs_golfcourse",
        "code": "GRG-105",
        "name": "Golf Course Road (Sec 27)",
        "area": "Cyber Hub → Sector 54",
        "bypass": "Clear & Open for 4-Wheelers",
        "lat": 28.4575,
        "lng": 77.0968,
        "road_width": "Wide 6-Lane",
        "drain_cleaned": True,
        "cleaner_team": "Cleaner Unit #D-05",
        "storm_depth_cm": 12,
        "pump_assigned": True
    },
    {
        "id": "hs_subhash",
        "code": "GRG-106",
        "name": "Subhash Chowk (Sohna Rd)",
        "area": "Sohna Rd → Sector 48",
        "bypass": "Golf Course Ext. Road",
        "lat": 28.4283,
        "lng": 77.0398,
        "road_width": "Wide 6-Lane",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-06",
        "storm_depth_cm": 85,
        "pump_assigned": False
    },
    {
        "id": "hs_sheetla",
        "code": "GRG-107",
        "name": "Sheetla Mata Road",
        "area": "Sector 5 → Old Gurugram",
        "bypass": "Palam Vihar Wide Link",
        "lat": 28.4754,
        "lng": 77.0315,
        "road_width": "Narrow 2-Lane",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-07",
        "storm_depth_cm": 80,
        "pump_assigned": False
    },
    {
        "id": "hs_narsinghpur",
        "code": "GRG-108",
        "name": "Narsinghpur Stretch (NH-48)",
        "area": "NH-48 → Manesar Approach",
        "bypass": "Dwarka Expressway Wide Rd",
        "lat": 28.4024,
        "lng": 76.9796,
        "road_width": "Service Lane",
        "drain_cleaned": False,
        "cleaner_team": "Cleaner Unit #D-08",
        "storm_depth_cm": 145,
        "pump_assigned": False
    }
]

INITIAL_VEHICLES = [
    {
        "id": "TANKER-101",
        "name": "Super Sucker Tanker #1",
        "category": "TANKER",
        "category_label": "Water Suction Tanker",
        "icon": "fa-truck-droplet",
        "driver": "Rajesh Sharma",
        "route": "Sector 33 → Rajiv Chowk",
        "lat": 28.4565,
        "lng": 77.0460,
        "status": "OPEN"
    },
    {
        "id": "TANKER-102",
        "name": "High-Flow Suction Tanker #2",
        "category": "TANKER",
        "category_label": "Water Suction Tanker",
        "icon": "fa-truck-droplet",
        "driver": "Ramesh Hooda",
        "route": "Pumping at Hero Honda Chowk",
        "lat": 28.4275,
        "lng": 77.0045,
        "status": "OCCUPIED"
    },
    {
        "id": "AMB-201",
        "name": "ALS Flood Ambulance #1",
        "category": "AMBULANCE",
        "category_label": "Ambulance",
        "icon": "fa-truck-medical",
        "driver": "Dr. Karanvir & Team",
        "route": "Medanta Emergency Standby",
        "lat": 28.4415,
        "lng": 77.0445,
        "status": "OPEN"
    },
    {
        "id": "AMB-202",
        "name": "Critical Care Ambulance #2",
        "category": "AMBULANCE",
        "category_label": "Ambulance",
        "icon": "fa-truck-medical",
        "driver": "Sunil Yadav",
        "route": "Huda City Centre Metro",
        "lat": 28.4605,
        "lng": 77.0740,
        "status": "OPEN"
    },
    {
        "id": "BOAT-301",
        "name": "SDRF Inflatable Boat #1",
        "category": "BOAT",
        "category_label": "Rescue Boat",
        "icon": "fa-ship",
        "driver": "Capt. Mandeep Singh",
        "route": "NH-48 Narsinghpur Stretch",
        "lat": 28.4050,
        "lng": 76.9820,
        "status": "OPEN"
    },
    {
        "id": "BOAT-302",
        "name": "SDRF Zodiac Boat #2",
        "category": "BOAT",
        "category_label": "Rescue Boat",
        "icon": "fa-ship",
        "driver": "Hawa Singh",
        "route": "Rajiv Chowk Underpass",
        "lat": 28.4435,
        "lng": 77.0320,
        "status": "OCCUPIED"
    },
    {
        "id": "QRV-401",
        "name": "MCG Quick Response 4x4 #1",
        "category": "QRV",
        "category_label": "Quick Response Vehicle",
        "icon": "fa-bolt",
        "driver": "Suresh Khatri",
        "route": "Sector 46 DHBVN Substation",
        "lat": 28.4360,
        "lng": 77.0580,
        "status": "OPEN"
    },
    {
        "id": "QRV-402",
        "name": "Traffic & Tow QRV #2",
        "category": "QRV",
        "category_label": "Quick Response Vehicle",
        "icon": "fa-bolt",
        "driver": "Naresh Tanwar",
        "route": "Golf Course Road Patrol",
        "lat": 28.4620,
        "lng": 77.0940,
        "status": "OPEN"
    }
]

INITIAL_SOS_REQUESTS = [
    {
        "id": "SOS-101",
        "person": "Sanjay Mehta",
        "spot_id": "hs_rajiv",
        "location": "Rajiv Chowk Underpass",
        "issue": "Vehicle Stuck in Deep Floodwater",
        "note": "Water rising near underpass ramp (115 cm), need suction tanker & tow.",
        "time_reported": "2 mins ago",
        "lat": 28.4456,
        "lng": 77.0339,
        "assigned_truck": None,
        "status": "PENDING"
    },
    {
        "id": "SOS-102",
        "person": "Ritu Verma",
        "spot_id": "hs_medanta",
        "location": "Medanta Hospital Road (Sec 38)",
        "issue": "Medical / Ambulance Evacuation",
        "note": "Patient vehicle blocked by waterlogging outside Gate 2.",
        "time_reported": "5 mins ago",
        "lat": 28.4389,
        "lng": 77.0424,
        "assigned_truck": None,
        "status": "PENDING"
    },
    {
        "id": "SOS-103",
        "person": "Deepak Khandelwal",
        "spot_id": "hs_herohonda",
        "location": "Hero Honda Chowk",
        "issue": "Urgent Water Suction Tanker Needed",
        "note": "Service lane completely submerged, traffic backed up.",
        "time_reported": "9 mins ago",
        "lat": 28.4258,
        "lng": 77.0019,
        "assigned_truck": None,
        "status": "PENDING"
    }
]

GURUGRAM_LANDMARKS = {
    "loc_cyberhub": {"name": "DLF Cyber Hub", "lat": 28.4946, "lng": 77.0888},
    "loc_iffco": {"name": "IFFCO Chowk Metro", "lat": 28.4773, "lng": 77.0689},
    "loc_huda": {"name": "Huda City Centre", "lat": 28.4593, "lng": 77.0724},
    "loc_sec29": {"name": "Sector 29 Market", "lat": 28.4682, "lng": 77.0635},
    "loc_golf": {"name": "Golf Course Road (Sec 27)", "lat": 28.4575, "lng": 77.0968},
    "loc_rajiv": {"name": "Rajiv Chowk", "lat": 28.4449, "lng": 77.0345},
    "loc_sohna": {"name": "Sohna Road (Subhash Chowk)", "lat": 28.4283, "lng": 77.0398},
    "loc_medanta": {"name": "Medanta Hospital (Sec 38)", "lat": 28.4394, "lng": 77.0416},
    "loc_herohonda": {"name": "Hero Honda Chowk", "lat": 28.4265, "lng": 77.0031}
}

def seed_database(db: Session):
    """Populates the database with initial records if empty."""
    if db.query(Hotspot).count() == 0:
        for spot_data in INITIAL_HOTSPOTS:
            db.add(Hotspot(**spot_data))
        db.commit()

    if db.query(Vehicle).count() == 0:
        for v_data in INITIAL_VEHICLES:
            db.add(Vehicle(**v_data))
        db.commit()

    if db.query(SosRequest).count() == 0:
        for sos_data in INITIAL_SOS_REQUESTS:
            db.add(SosRequest(**sos_data))
        db.commit()

    if db.query(WeatherState).count() == 0:
        db.add(WeatherState(
            id=1,
            scenario="storm",
            temperature=26.4,
            feels_like=29.1,
            rain_mm_hr=133.0,
            rain_bar_pct="95%",
            wind_speed=38.0,
            wind_direction="SW",
            humidity=94,
            visibility_km=1.8,
            alert_level="RED ALERT: EXTREME CLOUDBURST",
            advisory="Avoid NH-48 Underpasses (Rajiv & Hero Honda Chowk). Take Wide Golf Course Rd.",
            last_synced="Initial Cached IMD Telemetry"
        ))
        db.commit()
