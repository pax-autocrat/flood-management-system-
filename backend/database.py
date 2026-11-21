"""
JalRakshak NCR — Database & Persistence Engine (Phase 1)
Engineered for Team NeerNetra (SustainX 2026)
Provides thread-safe SQLite persistence with WAL mode, foreign keys,
and automatic table creation and seeding.
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jalrakshak.db")

def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like Row access and WAL enabled."""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_cursor(commit: bool = False):
    """Context manager yielding a cursor and handling commit/close cleanly."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    finally:
        conn.close()

def init_db():
    """Initializes schema and runs default seeds."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Agencies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agencies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        contact_number TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT NOT NULL DEFAULT 'CITIZEN',
        agency_code TEXT,
        badge_number TEXT,
        is_verified INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (agency_code) REFERENCES agencies(code) ON DELETE SET NULL
    );
    """)

    # 3. OTP Store Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_store (
        phone TEXT PRIMARY KEY,
        otp_hash TEXT NOT NULL,
        expires_at REAL NOT NULL,
        attempts INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    # 4. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        actor_id TEXT,
        actor_name TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        action TEXT NOT NULL,
        target_entity TEXT NOT NULL,
        target_id TEXT NOT NULL,
        payload_json TEXT,
        ip_address TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 5. Hotspots Persistence Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hotspots_db (
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        area TEXT NOT NULL,
        bypass TEXT,
        road_width TEXT,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        drain_cleaned INTEGER DEFAULT 0,
        pump_assigned INTEGER DEFAULT 0,
        cleaner_team TEXT,
        storm_depth_cm INTEGER DEFAULT 100,
        current_depth_cm INTEGER DEFAULT 100,
        last_updated TEXT NOT NULL
    );
    """)

    # 6. Master Stormwater Drains Table (36 Primary Trunks)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stormwater_drains (
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        catchment_leg TEXT NOT NULL,
        outfall_destination TEXT NOT NULL,
        length_km REAL NOT NULL,
        silt_depth_cm INTEGER DEFAULT 45,
        status TEXT NOT NULL DEFAULT 'CLOGGED',
        contractor_name TEXT,
        contractor_phone TEXT,
        assigned_hotspot_id TEXT,
        dredged_volume_m3 REAL DEFAULT 0.0,
        target_volume_m3 REAL DEFAULT 850.0,
        last_cleaned_at TEXT,
        updated_at TEXT NOT NULL
    );
    """)

    # 7. Desilting Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS desilting_audit_logs (
        id TEXT PRIMARY KEY,
        drain_id TEXT NOT NULL,
        contractor_name TEXT NOT NULL,
        inspector_name TEXT,
        dredged_volume_m3 REAL NOT NULL,
        photo_before_url TEXT,
        photo_after_url TEXT,
        verified_by_inspector INTEGER DEFAULT 0,
        notes TEXT,
        logged_at TEXT NOT NULL,
        FOREIGN KEY (drain_id) REFERENCES stormwater_drains(id) ON DELETE CASCADE
    );
    """)

    # 8. Emergency Rescue Vehicles Table (Fleet Transponders)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rescue_vehicles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        category_label TEXT NOT NULL,
        icon TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        driver_phone TEXT NOT NULL,
        current_route TEXT,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN',
        capacity_liters INTEGER DEFAULT 0,
        speed_kmh REAL DEFAULT 0.0,
        heading_deg REAL DEFAULT 0.0,
        last_ping TEXT NOT NULL
    );
    """)

    # 9. Citizen SOS Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sos_incidents (
        id TEXT PRIMARY KEY,
        caller_name TEXT NOT NULL,
        caller_phone TEXT NOT NULL,
        hotspot_id TEXT,
        location_name TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        issue_type TEXT NOT NULL,
        urgency TEXT NOT NULL DEFAULT 'MEDIUM',
        people_count INTEGER DEFAULT 1,
        has_medical_emergency INTEGER DEFAULT 0,
        water_level_gauge TEXT,
        landmark_notes TEXT,
        photo_url TEXT,
        assigned_vehicle_id TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        created_at TEXT NOT NULL,
        dispatched_at TEXT,
        resolved_at TEXT,
        FOREIGN KEY (assigned_vehicle_id) REFERENCES rescue_vehicles(id) ON DELETE SET NULL
    );
    """)

    # 10. Crowdsourced Waterlogging & Hazard Reports Table (Jal-Doot)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crowdsourced_reports (
        id TEXT PRIMARY KEY,
        reported_by_id TEXT,
        reporter_name TEXT NOT NULL,
        reporter_phone TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        location_address TEXT NOT NULL,
        estimated_depth_cm INTEGER DEFAULT 30,
        is_manhole_open INTEGER DEFAULT 0,
        is_wire_hazard INTEGER DEFAULT 0,
        is_submerged_vehicle INTEGER DEFAULT 0,
        photo_url TEXT,
        has_exif_gps INTEGER DEFAULT 0,
        ai_confidence_score REAL DEFAULT 0.85,
        status TEXT NOT NULL DEFAULT 'VERIFIED_AI',
        upvotes INTEGER DEFAULT 1,
        downvotes INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (reported_by_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 11. DHBVN Electrical Substation Hazard Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS electrical_hazards (
        id TEXT PRIMARY KEY,
        feeder_code TEXT NOT NULL,
        substation_name TEXT NOT NULL,
        area TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        voltage_kv REAL DEFAULT 11.0,
        water_depth_near_feeder_cm INTEGER DEFAULT 0,
        power_cut_requested INTEGER DEFAULT 0,
        power_cut_executed INTEGER DEFAULT 0,
        requested_by TEXT,
        requested_at TEXT,
        cut_executed_at TEXT,
        substation_phone TEXT NOT NULL
    );
    """)

    # 12. Emergency Shelters & Safe Dry Parking Zones (MLCP)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emergency_shelters (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        shelter_type TEXT NOT NULL,
        address TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        capacity_people INTEGER DEFAULT 200,
        capacity_vehicles INTEGER DEFAULT 0,
        current_occupancy INTEGER DEFAULT 0,
        has_drinking_water INTEGER DEFAULT 1,
        has_power_backup INTEGER DEFAULT 1,
        has_first_aid INTEGER DEFAULT 1,
        contact_person TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """)

    # 13. Automated Underpass Boom Barriers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS underpass_barriers (
        id TEXT PRIMARY KEY,
        hotspot_id TEXT NOT NULL,
        location_name TEXT NOT NULL,
        barrier_state TEXT NOT NULL DEFAULT 'OPEN',
        trigger_threshold_cm INTEGER DEFAULT 35,
        closed_by TEXT,
        closed_at TEXT,
        last_inspected TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed Default Agencies
    agencies_seed = [
        ("MCG", "Municipal Corporation of Gurugram", "1800-180-1817"),
        ("GMDA", "Gurugram Metropolitan Development Authority", "0124-2746600"),
        ("NHAI", "National Highways Authority of India (NH-48)", "1033"),
        ("DHBVN", "Dakshin Haryana Bijli Vitran Nigam", "1912"),
        ("SDRF", "State Disaster Response Force Haryana", "112"),
        ("POLICE", "Gurugram Traffic Police", "1095")
    ]
    for code, name, phone in agencies_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO agencies (id, code, name, contact_number, created_at)
        VALUES (?, ?, ?, ?, ?);
        """, (str(uuid.uuid4()), code, name, phone, datetime.now(timezone.utc).isoformat()))

    # Seed Default Hotspots (8 primary arterial nodes)
    hotspots_seed = [
        ('hs_rajiv', 'GRG-101', 'Rajiv Chowk Underpass', 'NH-48 → Sohna Road', 'Golf Course Rd → SPR', 'Wide 6-Lane', 28.4449, 77.0345, 0, 0, 'Cleaner Unit #D-01', 115),
        ('hs_herohonda', 'GRG-102', 'Hero Honda Chowk', 'NH-48 → Sector 34/37', 'SPR Wide Highway', 'Wide 6-Lane', 28.4265, 77.0031, 0, 0, 'Cleaner Unit #D-02', 135),
        ('hs_medanta', 'GRG-103', 'Medanta Hospital Road', 'Sector 38 → Subhash Chowk', 'Huda City Centre Wide Rd', '4-Lane Road', 28.4394, 77.0416, 0, 0, 'Cleaner Unit #D-03', 90),
        ('hs_iffco', 'GRG-104', 'IFFCO Chowk Metro', 'MG Road → Cyber Hub', 'MG Road Elevated Corridor', 'Wide 6-Lane', 28.4773, 77.0689, 1, 1, 'Cleaner Unit #D-04', 35),
        ('hs_golfcourse', 'GRG-105', 'Golf Course Road (Sec 27)', 'Cyber Hub → Sector 54', 'Clear & Open for 4-Wheelers', 'Wide 6-Lane', 28.4575, 77.0968, 1, 1, 'Cleaner Unit #D-05', 12),
        ('hs_subhash', 'GRG-106', 'Subhash Chowk (Sohna Rd)', 'Sohna Rd → Sector 48', 'Golf Course Ext. Road', 'Wide 6-Lane', 28.4283, 77.0398, 0, 0, 'Cleaner Unit #D-06', 85),
        ('hs_sheetla', 'GRG-107', 'Sheetla Mata Road', 'Sector 5 → Old Gurugram', 'Palam Vihar Wide Link', 'Narrow 2-Lane', 28.4754, 77.0315, 0, 0, 'Cleaner Unit #D-07', 80),
        ('hs_narsinghpur', 'GRG-108', 'Narsinghpur Stretch (NH-48)', 'NH-48 → Manesar Approach', 'Dwarka Expressway Wide Rd', 'Service Lane', 28.4024, 76.9796, 0, 0, 'Cleaner Unit #D-08', 145)
    ]
    now_iso = datetime.now(timezone.utc).isoformat()
    for row in hotspots_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO hotspots_db 
        (id, code, name, area, bypass, road_width, lat, lng, drain_cleaned, pump_assigned, cleaner_team, storm_depth_cm, current_depth_cm, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (*row, row[-1], now_iso))

    # Seed All 36 Master Stormwater Drains (Leg 1, Leg 2, Leg 3)
    drains_36_seed = [
        # --- LEG 1: EAST / GOLF COURSE SPINE (12 Trunks) ---
        ('DR-01', 'LEG1-01', 'DLF Phase 1 Aravalli Outfall', 'LEG 1: EAST GOLF COURSE', 'Chakkarpur Silt Basin', 3.8, 48, 'CLOGGED', 'Shree Ram Infra Ltd', '+91-9811223344', 'hs_golfcourse', 210.0, 750.0),
        ('DR-02', 'LEG1-02', 'Sector 54 Rapid Metro Outfall', 'LEG 1: EAST GOLF COURSE', 'Wazirabad Lake Outfall', 2.6, 25, 'CLEANED', 'Shree Ram Infra Ltd', '+91-9811223344', 'hs_golfcourse', 620.0, 620.0),
        ('DR-03', 'LEG1-03', 'Sector 42/43 Golf Course Lateral', 'LEG 1: EAST GOLF COURSE', 'Sector 43 Sump Basin', 4.1, 52, 'CLOGGED', 'Apex Desilting Works', '+91-9811445566', 'hs_golfcourse', 140.0, 800.0),
        ('DR-04', 'LEG1-04', 'Sector 27 Galleria Culvert', 'LEG 1: EAST GOLF COURSE', 'Leg 1 Master Spine', 1.9, 15, 'CLEANED', 'Apex Desilting Works', '+91-9811445566', 'hs_golfcourse', 450.0, 450.0),
        ('DR-05', 'LEG1-05', 'Sector 28 DLF Phase 4 Lateral', 'LEG 1: EAST GOLF COURSE', 'Chakkarpur Bundh Conduit', 3.2, 40, 'DESILTING_IN_PROGRESS', 'Apex Desilting Works', '+91-9811445566', 'hs_golfcourse', 380.0, 700.0),
        ('DR-06', 'LEG1-06', 'DLF Phase 5 Club Drive Confluence', 'LEG 1: EAST GOLF COURSE', 'Golf Course Master Conduit', 2.4, 20, 'CLEANED', 'Shree Ram Infra Ltd', '+91-9811223344', 'hs_golfcourse', 550.0, 550.0),
        ('DR-07', 'LEG1-07', 'Genpact Chowk Underpass Sump', 'LEG 1: EAST GOLF COURSE', 'DLF Underpass Drain', 1.5, 30, 'CLEANED', 'MCG Direct Crew A', '+91-9811001122', 'hs_golfcourse', 390.0, 390.0),
        ('DR-08', 'LEG1-08', 'Bristol Chowk / Sikanderpur Link', 'LEG 1: EAST GOLF COURSE', 'MG Road Interceptor', 3.0, 55, 'CLOGGED', 'Shree Ram Infra Ltd', '+91-9811223344', 'hs_iffco', 180.0, 900.0),
        ('DR-09', 'LEG1-09', 'Sector 56 Kendriya Vihar Trunk', 'LEG 1: EAST GOLF COURSE', 'Ghata Spillway Conduit', 4.5, 60, 'CLOGGED', 'Haryana Civil Works', '+91-9811889900', 'hs_golfcourse', 120.0, 950.0),
        ('DR-10', 'LEG1-10', 'Ghata Village Silt Check Dam', 'LEG 1: EAST GOLF COURSE', 'Aravalli Ridge Inceptor', 5.2, 65, 'CLOGGED', 'Haryana Civil Works', '+91-9811889900', 'hs_golfcourse', 80.0, 1200.0),
        ('DR-11', 'LEG1-11', 'Aravalli Biodiversity Park Sump', 'LEG 1: EAST GOLF COURSE', 'Nathupur Outfall Drain', 2.8, 18, 'CLEANED', 'MCG Direct Crew B', '+91-9811001122', 'hs_iffco', 600.0, 600.0),
        ('DR-12', 'LEG1-12', 'Sector 53 Sector Road Outfall', 'LEG 1: EAST GOLF COURSE', 'SunCity Sump Link', 2.1, 42, 'DESILTING_IN_PROGRESS', 'Apex Desilting Works', '+91-9811445566', 'hs_golfcourse', 290.0, 500.0),

        # --- LEG 2: CENTRAL SPINE & OLD GURUGRAM (12 Trunks) ---
        ('DR-13', 'LEG2-01', 'IFFCO Chowk Metro Storm Lateral', 'LEG 2: CENTRAL SPINE', 'Leg 2 Central Spine', 3.4, 20, 'CLEANED', 'Gurugram Desilting Corp', '+91-9811556677', 'hs_iffco', 780.0, 780.0),
        ('DR-14', 'LEG2-02', 'Sheetla Mata Temple Outfall', 'LEG 2: CENTRAL SPINE', 'Old Gurugram Najafgarh Link', 4.0, 58, 'CLOGGED', 'Gurugram Desilting Corp', '+91-9811556677', 'hs_sheetla', 150.0, 850.0),
        ('DR-15', 'LEG2-03', 'Old Railway Road Drain (Sec 4/7)', 'LEG 2: CENTRAL SPINE', 'Basai Pumping Sump', 3.6, 62, 'CLOGGED', 'Kisan Earthmovers', '+91-9811334455', 'hs_sheetla', 90.0, 920.0),
        ('DR-16', 'LEG2-04', 'Sector 14 HUDA Market Confluence', 'LEG 2: CENTRAL SPINE', 'Leg 2 Trunk Drain', 2.9, 45, 'DESILTING_IN_PROGRESS', 'Kisan Earthmovers', '+91-9811334455', 'hs_iffco', 340.0, 680.0),
        ('DR-17', 'LEG2-05', 'Sector 15 Part 1 Drain Link', 'LEG 2: CENTRAL SPINE', 'Civil Hospital Outfall', 2.2, 50, 'CLOGGED', 'Kisan Earthmovers', '+91-9811334455', 'hs_rajiv', 110.0, 550.0),
        ('DR-18', 'LEG2-06', 'Sector 17/18 Industrial Outfall', 'LEG 2: CENTRAL SPINE', 'Delhi Border Najafgarh Drain', 4.8, 38, 'CLEANED', 'Gurugram Desilting Corp', '+91-9811556677', 'hs_iffco', 820.0, 820.0),
        ('DR-19', 'LEG2-07', 'Sector 22/23 Palam Vihar Lateral', 'LEG 2: CENTRAL SPINE', 'Dundahera Master Link', 4.3, 54, 'CLOGGED', 'Northern Desilters', '+91-9811667788', 'hs_sheetla', 190.0, 880.0),
        ('DR-20', 'LEG2-08', 'Sector 29 Leisure Valley Basin', 'LEG 2: CENTRAL SPINE', 'Huda City Centre Conduit', 3.1, 22, 'CLEANED', 'MCG Direct Crew C', '+91-9811001122', 'hs_iffco', 640.0, 640.0),
        ('DR-21', 'LEG2-09', 'Sector 31 HUDA Sump Drain', 'LEG 2: CENTRAL SPINE', 'NH-48 Crossing Culvert', 2.5, 48, 'DESILTING_IN_PROGRESS', 'Northern Desilters', '+91-9811667788', 'hs_rajiv', 260.0, 600.0),
        ('DR-22', 'LEG2-10', 'Sector 32 Institutional Area Link', 'LEG 2: CENTRAL SPINE', 'Medanta Feeder Sump', 2.7, 46, 'CLOGGED', 'Northern Desilters', '+91-9811667788', 'hs_medanta', 180.0, 620.0),
        ('DR-23', 'LEG2-11', 'Basai Road Pumping Culvert', 'LEG 2: CENTRAL SPINE', 'Basai Water Works Spillway', 5.0, 70, 'CLOGGED', 'Kisan Earthmovers', '+91-9811334455', 'hs_sheetla', 100.0, 1100.0),
        ('DR-24', 'LEG2-12', 'Pataudi Road Railway Underpass Drain', 'LEG 2: CENTRAL SPINE', 'Railway Culvert #14', 3.3, 65, 'CLOGGED', 'Northern Desilters', '+91-9811667788', 'hs_sheetla', 70.0, 800.0),

        # --- LEG 3: BADSHAHPUR MASTER TRUNK & KHANDSA CULVERT (12 Trunks) ---
        ('DR-25', 'LEG3-01', 'Khandsa Box Culvert (Trunk Bottleneck)', 'LEG 3: BADSHAHPUR TRUNK', 'Najafgarh Basin Master', 6.5, 75, 'CLOGGED', 'Haryana Drainage Consortium', '+91-9811778899', 'hs_herohonda', 120.0, 2400.0),
        ('DR-26', 'LEG3-02', 'Hero Honda Chowk Master Sump', 'LEG 3: BADSHAHPUR TRUNK', 'Khandsa Conduit Entry', 3.8, 68, 'CLOGGED', 'Haryana Drainage Consortium', '+91-9811778899', 'hs_herohonda', 180.0, 1500.0),
        ('DR-27', 'LEG3-03', 'Rajiv Chowk Underpass Collector', 'LEG 3: BADSHAHPUR TRUNK', 'Badshahpur Leg 3 Lateral', 3.5, 58, 'CLOGGED', 'Haryana Drainage Consortium', '+91-9811778899', 'hs_rajiv', 210.0, 1100.0),
        ('DR-28', 'LEG3-04', 'Narsinghpur Stretch Culvert (NH-48)', 'LEG 3: BADSHAHPUR TRUNK', 'Khandsa Backwater Sink', 4.2, 80, 'CLOGGED', 'Pace Infrastructures', '+91-9811990011', 'hs_narsinghpur', 90.0, 1600.0),
        ('DR-29', 'LEG3-05', 'Subhash Chowk (Sohna Rd) Midstream', 'LEG 3: BADSHAHPUR TRUNK', 'Badshahpur Conduit Mid', 3.9, 45, 'DESILTING_IN_PROGRESS', 'Pace Infrastructures', '+91-9811990011', 'hs_subhash', 420.0, 950.0),
        ('DR-30', 'LEG3-06', 'Medanta Hospital Road Collector (Sec 38)', 'LEG 3: BADSHAHPUR TRUNK', 'Subhash Chowk Interceptor', 2.8, 52, 'CLOGGED', 'Pace Infrastructures', '+91-9811990011', 'hs_medanta', 160.0, 700.0),
        ('DR-31', 'LEG3-07', 'Sector 48 CD Chowk Feeder', 'LEG 3: BADSHAHPUR TRUNK', 'Sohna Road Master Channel', 3.1, 40, 'CLEANED', 'MCG Direct Crew D', '+91-9811001122', 'hs_subhash', 610.0, 610.0),
        ('DR-32', 'LEG3-08', 'Sector 34/37 Industrial Outfall', 'LEG 3: BADSHAHPUR TRUNK', 'Hero Honda Secondary Link', 4.6, 55, 'CLOGGED', 'Pace Infrastructures', '+91-9811990011', 'hs_herohonda', 230.0, 1050.0),
        ('DR-33', 'LEG3-09', 'Southern Peripheral Road (SPR) Trunk', 'LEG 3: BADSHAHPUR TRUNK', 'Vatika Sump Outfall', 6.0, 35, 'CLEANED', 'National Highway Drainers', '+91-9811112233', 'hs_herohonda', 1250.0, 1250.0),
        ('DR-34', 'LEG3-10', 'Sector 70/71 Vatika Chowk Conduit', 'LEG 3: BADSHAHPUR TRUNK', 'SPR Trunk Feeder', 3.7, 44, 'DESILTING_IN_PROGRESS', 'National Highway Drainers', '+91-9811112233', 'hs_subhash', 380.0, 750.0),
        ('DR-35', 'LEG3-11', 'Badshahpur Village Check Dam Spillway', 'LEG 3: BADSHAHPUR TRUNK', 'Aravalli Runoff Basin', 5.5, 62, 'CLOGGED', 'Haryana Drainage Consortium', '+91-9811778899', 'hs_subhash', 140.0, 1400.0),
        ('DR-36', 'LEG3-12', 'Najafgarh Drain Master Outfall Boundary', 'LEG 3: BADSHAHPUR TRUNK', 'Yamuna Basin Ultimate Outfall', 8.2, 70, 'CLOGGED', 'Haryana Drainage Consortium', '+91-9811778899', 'hs_herohonda', 320.0, 3200.0)
    ]

    for d in drains_36_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO stormwater_drains 
        (id, code, name, catchment_leg, outfall_destination, length_km, silt_depth_cm, status, contractor_name, contractor_phone, assigned_hotspot_id, dredged_volume_m3, target_volume_m3, last_cleaned_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (*d, now_iso, now_iso))

    # Seed 8 Emergency Fleet Rescue Vehicles
    vehicles_seed = [
        ('TANKER-101', 'Super Sucker Tanker #1', 'TANKER', 'Water Suction Tanker', 'fa-truck-droplet', 'Rajesh Sharma', '+91-9811002201', 'Sector 33 → Rajiv Chowk', 28.4565, 77.0460, 'OPEN', 10000),
        ('TANKER-102', 'High-Flow Suction Tanker #2', 'TANKER', 'Water Suction Tanker', 'fa-truck-droplet', 'Ramesh Hooda', '+91-9811002202', 'Pumping at Hero Honda Chowk', 28.4275, 77.0045, 'OCCUPIED', 12000),
        ('AMB-201', 'ALS Flood Ambulance #1', 'AMBULANCE', 'Ambulance', 'fa-truck-medical', 'Dr. Karanvir & Team', '+91-9811002203', 'Medanta Emergency Standby', 28.4415, 77.0445, 'OPEN', 0),
        ('AMB-202', 'Critical Care Ambulance #2', 'AMBULANCE', 'Ambulance', 'fa-truck-medical', 'Sunil Yadav', '+91-9811002204', 'Huda City Centre Metro', 28.4605, 77.0740, 'OPEN', 0),
        ('BOAT-301', 'SDRF Inflatable Boat #1', 'BOAT', 'Rescue Boat', 'fa-ship', 'Capt. Mandeep Singh', '+91-9811002205', 'NH-48 Narsinghpur Stretch', 28.4050, 76.9820, 'OPEN', 0),
        ('BOAT-302', 'SDRF Zodiac Boat #2', 'BOAT', 'Rescue Boat', 'fa-ship', 'Hawa Singh', '+91-9811002206', 'Rajiv Chowk Underpass', 28.4435, 77.0320, 'OCCUPIED', 0),
        ('QRV-401', 'MCG Quick Response 4x4 #1', 'QRV', 'Quick Response Vehicle', 'fa-bolt', 'Suresh Khatri', '+91-9811002207', 'Sector 46 DHBVN Substation', 28.4360, 77.0580, 'OPEN', 0),
        ('QRV-402', 'Traffic & Tow QRV #2', 'QRV', 'Quick Response Vehicle', 'fa-bolt', 'Naresh Tanwar', '+91-9811002208', 'Golf Course Road Patrol', 28.4620, 77.0940, 'OPEN', 0)
    ]
    for v in vehicles_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO rescue_vehicles 
        (id, name, category, category_label, icon, driver_name, driver_phone, current_route, lat, lng, status, capacity_liters, last_ping)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (*v, now_iso))

    # Seed 3 Initial Distress SOS Incidents
    sos_seed = [
        ('SOS-101', 'Sanjay Mehta', '+91-9811223344', 'hs_rajiv', 'Rajiv Chowk Underpass', 28.4456, 77.0339, 'Vehicle Stuck in Deep Floodwater', 'CRITICAL', 2, 0, 'Door Sill', 'Water rising near underpass ramp (115 cm), need suction tanker & tow.', None, 'PENDING'),
        ('SOS-102', 'Ritu Verma', '+91-9811334455', 'hs_medanta', 'Medanta Hospital Road (Sec 38)', 28.4389, 77.0424, 'Medical / Ambulance Evacuation', 'HIGH', 1, 1, 'Tire Level', 'Patient vehicle blocked by waterlogging outside Gate 2.', None, 'PENDING'),
        ('SOS-103', 'Deepak Khandelwal', '+91-9811445566', 'hs_herohonda', 'Hero Honda Chowk', 28.4258, 77.0019, 'Urgent Water Suction Tanker Needed', 'HIGH', 1, 0, 'Window Level', 'Service lane completely submerged, traffic backed up.', None, 'PENDING')
    ]
    for s in sos_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO sos_incidents
        (id, caller_name, caller_phone, hotspot_id, location_name, lat, lng, issue_type, urgency, people_count, has_medical_emergency, water_level_gauge, landmark_notes, assigned_vehicle_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (*s, now_iso))

    # Seed Initial Verified Crowdsourced Hazard Reports (Jal-Doot)
    exp_iso = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
    crowd_seed = [
        ('CR-001', 'Manish Goel', '+91-9811554433', 28.4535, 77.0515, 'Sector 31 Market Service Lane', 45, 1, 0, 0, 'https://s3.jalrakshak.in/reports/cr001.jpg', 1, 0.92, 'VERIFIED_AI', 5, 0),
        ('CR-002', 'Sunita Malik', '+91-9811665544', 28.5025, 77.0345, 'Palam Vihar Vyapar Kendra Road', 35, 0, 0, 1, 'https://s3.jalrakshak.in/reports/cr002.jpg', 1, 0.88, 'CONFIRMED_COMMUNITY', 8, 1),
        ('CR-003', 'Vikas Ahlawat', '+91-9811776655', 28.4235, 77.1030, 'Sector 56 Kendriya Vihar Gate 2', 40, 0, 1, 0, 'https://s3.jalrakshak.in/reports/cr003.jpg', 1, 0.94, 'VERIFIED_AI', 4, 0)
    ]
    for c in crowd_seed:
        cursor.execute("""
        INSERT OR REPLACE INTO crowdsourced_reports
        (id, reporter_name, reporter_phone, lat, lng, location_address, estimated_depth_cm, is_manhole_open, is_wire_hazard, is_submerged_vehicle, photo_url, has_exif_gps, ai_confidence_score, status, upvotes, downvotes, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (*c, now_iso, exp_iso))

    # Seed DHBVN Electrical Substation Feeders
    feeders_seed = [
        ('FDR-46-01', 'FDR-SEC46-11KV', 'Sector 46 11kV Substation', 'Sector 46 / Bakhtawar Chowk', 28.4360, 77.0580, 11.0, 20, 0, 0, '1912 / +91-9811005566'),
        ('FDR-HH-02', 'FDR-HERO-11KV', 'Hero Honda Industrial 11kV Feeder', 'Sector 34/37 Industrial Area', 28.4270, 77.0040, 11.0, 48, 0, 0, '1912 / +91-9811005566'),
        ('FDR-RJ-03', 'FDR-RAJIV-11KV', 'Rajiv Chowk Service Lane Transformer', 'NH-48 Rajiv Chowk Exit', 28.4452, 77.0340, 11.0, 35, 0, 0, '1912 / +91-9811005566'),
        ('FDR-DLF-04', 'FDR-DLF-11KV', 'DLF Phase 1 Aravalli Feeder', 'Sikanderpur / MG Road', 28.4810, 77.0920, 11.0, 12, 0, 0, '1912 / +91-9811005566')
    ]
    for f in feeders_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO electrical_hazards
        (id, feeder_code, substation_name, area, lat, lng, voltage_kv, water_depth_near_feeder_cm, power_cut_requested, power_cut_executed, substation_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, f)

    # Seed Emergency Relief Shelters & Safe Dry Parking Sanctuaries (MLCP)
    shelters_seed = [
        ('SH-01', 'Tau Devi Lal Stadium Relief Shelter', 'RELIEF_CAMP', 'Sector 38, near Medanta Hospital, Gurugram', 28.4350, 77.0380, 1500, 0, 45, 1, 1, 1, 'MCG Relief Officer Sandeep', '1800-180-1817'),
        ('SH-02', 'Huda Gymkhana Club Relief Center', 'COMMUNITY_CENTER', 'Sector 29, opposite Leisure Valley, Gurugram', 28.4680, 77.0650, 500, 0, 20, 1, 1, 1, 'Facility Manager Huda', '1800-180-1817'),
        ('SH-03', 'Sector 29 Multi-Level Parking Sanctuary (MLCP)', 'MLCP_PARKING', 'Sector 29 Commercial Complex, Gurugram', 28.4690, 77.0630, 200, 1800, 620, 1, 1, 1, 'Parking Supt. Naresh', '+91-9811009911'),
        ('SH-04', 'DLF Cyber Hub Elevated MLCP Parking', 'MLCP_PARKING', 'DLF Cyber City, Sector 24, Gurugram', 28.4950, 77.0890, 100, 2500, 1100, 1, 1, 1, 'DLF Facilities Desk', '0124-4567890'),
        ('SH-05', 'Govt Girls Senior Secondary School', 'GOVT_SCHOOL', 'Jacobpura, Old Gurugram, 122001', 28.4720, 77.0280, 400, 0, 0, 1, 1, 1, 'Principal Office', '1800-180-1817')
    ]
    for s in shelters_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO emergency_shelters
        (id, name, shelter_type, address, lat, lng, capacity_people, capacity_vehicles, current_occupancy, has_drinking_water, has_power_backup, has_first_aid, contact_person, contact_phone, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        """, s)

    # Seed Automated Underpass Boom Barriers
    barriers_seed = [
        ('BAR-RAJIV-01', 'hs_rajiv', 'Rajiv Chowk Underpass South Ramp', 'OPEN', 35, now_iso),
        ('BAR-HERO-02', 'hs_herohonda', 'Hero Honda Chowk Main Tunnel', 'OPEN', 35, now_iso),
        ('BAR-MED-03', 'hs_medanta', 'Medanta Hospital Road Underpass', 'OPEN', 30, now_iso)
    ]
    for b in barriers_seed:
        cursor.execute("""
        INSERT OR IGNORE INTO underpass_barriers
        (id, hotspot_id, location_name, barrier_state, trigger_threshold_cm, last_inspected)
        VALUES (?, ?, ?, ?, ?, ?);
        """, b)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_FILE)
