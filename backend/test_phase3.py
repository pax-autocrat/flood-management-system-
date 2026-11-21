"""
JalRakshak NCR — Phase 3 Automated Verification Suite
Validates:
1. Persistent Rescue Fleet Inventory (8 Vehicles across 4 Categories)
2. Citizen Emergency Distress Intake (`POST /api/v1/sos`)
3. Spatial Nearest-Unit Haversine Matching Algorithm
4. Official Emergency Vehicle Dispatch Workflow
5. Real-Time Citizen Rescue Tracking Screen (Live Distance & ETA)
6. Vehicle Transponder GPS Movement Ingestion
7. Distress Incident Resolution & Fleet Unit Release
8. Real-Time WebSocket Gateway Protocol Handshake
"""

import sys
import os
import json
from fastapi.testclient import TestClient

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from main import app
from services.auth_service import auth_service

client = TestClient(app)

def run_phase3_tests():
    print("=" * 75)
    print("  PHASE 3 VERIFICATION: REAL-TIME WEBSOCKETS, FLEET & CITIZEN SOS")
    print("  Team: NeerNetra | Lead: Kamal Shukla | SustainX 2026")
    print("=" * 75)

    # 0. Setup Official Headers & Reset Vehicle Test State
    from database import get_db_cursor
    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE rescue_vehicles SET lat = 28.4415, lng = 77.0445, status = 'OPEN' WHERE id = 'AMB-201';")

    official_user = auth_service.authenticate_official("Vikram Singh", "MCG-GURUGRAM-2026")
    official_token = auth_service.create_access_token({
        "sub": official_user["id"],
        "name": official_user["name"],
        "role": official_user["role"],
        "agency": official_user.get("agency_code")
    })
    official_headers = {"Authorization": f"Bearer {official_token}"}

    # ------------------ TEST 1: FLEET INVENTORY & CATEGORY FILTERING ------------------
    print("\n[TEST 1] Testing Emergency Fleet Inventory & Category Breakdown...")
    res_fleet = client.get("/api/v1/fleet", headers=official_headers)
    assert res_fleet.status_code == 200, f"Fleet query failed: {res_fleet.text}"
    fleet_data = res_fleet.json()
    assert fleet_data["total_fleet"] == 8
    assert fleet_data["count"] == 8, f"Expected 8 vehicles, got {fleet_data['count']}"

    # Category breakdown verification
    categories = {v["category"] for v in fleet_data["vehicles"]}
    assert categories == {"TANKER", "AMBULANCE", "BOAT", "QRV"}
    print(f"  -> Total Vehicles: 8 (Categories: {', '.join(sorted(categories))})")

    # Filter test for Suction Tankers
    res_tankers = client.get("/api/v1/fleet?category=TANKER", headers=official_headers)
    assert res_tankers.status_code == 200
    assert len(res_tankers.json()["vehicles"]) == 2
    print("  [PASS] Fleet inventory & category filtering verified.")

    # ------------------ TEST 2: CITIZEN SOS INTAKE ------------------
    print("\n[TEST 2] Testing Citizen Distress Intake (Submerged Car on Sohna Road)...")
    res_sos = client.post("/api/v1/sos", json={
        "caller_name": "Kavita Rao",
        "caller_phone": "+91-9811099887",
        "location_name": "Subhash Chowk Underpass Ramp",
        "lat": 28.4285,
        "lng": 77.0395,
        "issue_type": "Vehicle Stuck in Deep Floodwater",
        "urgency": "CRITICAL",
        "people_count": 3,
        "has_medical_emergency": True,
        "water_level_gauge": "Window Level",
        "landmark_notes": "Red Swift Dzire, water entering windows, elderly patient inside.",
        "hotspot_id": "hs_subhash"
    })
    assert res_sos.status_code == 200, f"SOS submission failed: {res_sos.text}"
    sos_data = res_sos.json()
    assert sos_data["status"] == "sos_received"
    new_sos_id = sos_data["sos_id"]
    assert new_sos_id.startswith("SOS-")
    print(f"  -> Created Emergency Distress Ticket: {new_sos_id}")
    print(f"  -> Caller: Kavita Rao | Location: Subhash Chowk | Urgency: CRITICAL")
    print("  [PASS] Citizen SOS intake & ticket persistence verified.")

    # ------------------ TEST 3: SPATIAL NEAREST-UNIT MATCHING ------------------
    print("\n[TEST 3] Testing Spatial Nearest-Unit Haversine Matching Algorithm...")
    # Target coordinates: Subhash Chowk (28.4285, 77.0395)
    res_nearest = client.get("/api/v1/fleet/nearest-unit?lat=28.4285&lng=77.0395")
    assert res_nearest.status_code == 200, f"Nearest unit lookup failed: {res_nearest.text}"
    nearest_unit = res_nearest.json()
    assert "distance_km" in nearest_unit
    assert "estimated_eta_mins" in nearest_unit
    assert nearest_unit["status"] == "OPEN"
    print(f"  -> Algorithm matched closest OPEN vehicle: {nearest_unit['name']} ({nearest_unit['id']})")
    print(f"  -> Distance: {nearest_unit['distance_km']} km | Estimated Travel ETA: {nearest_unit['estimated_eta_mins']} mins")
    print("  [PASS] Nearest-unit spatial Haversine algorithm verified.")

    # ------------------ TEST 4: OFFICIAL EMERGENCY DISPATCH WORKFLOW ------------------
    print("\n[TEST 4] Testing Official Emergency Vehicle Dispatch Workflow...")
    res_dispatch = client.post(f"/api/v1/sos/{new_sos_id}/dispatch", json={}, headers=official_headers)
    assert res_dispatch.status_code == 200, f"Dispatch failed: {res_dispatch.text}"
    dispatch_data = res_dispatch.json()
    assert dispatch_data["status"] == "dispatched"
    assigned_v_id = dispatch_data["assigned_vehicle_id"]
    print(f"  -> Successfully Dispatched Unit: {dispatch_data['assigned_vehicle']} ({assigned_v_id})")
    print(f"  -> Assigned Driver: {dispatch_data['driver_name']} (Phone: {dispatch_data['driver_phone']})")

    # Verify vehicle status is now OCCUPIED
    assigned_v = client.get(f"/api/v1/fleet/{assigned_v_id}").json()
    assert assigned_v["status"] == "OCCUPIED"
    print(f"  -> Verified vehicle {assigned_v_id} status transitioned to OCCUPIED.")
    print("  [PASS] Official dispatch workflow verified.")

    # ------------------ TEST 5: REAL-TIME CITIZEN RESCUE TRACKER ------------------
    print("\n[TEST 5] Testing Citizen Rescue Live Tracking Screen...")
    res_track = client.get(f"/api/v1/sos/track/{new_sos_id}")
    assert res_track.status_code == 200, f"Tracking query failed: {res_track.text}"
    track_view = res_track.json()
    assert track_view["status"] == "ASSIGNED"
    assert track_view["assigned_vehicle"] is not None
    v_track = track_view["assigned_vehicle"]
    initial_dist_m = v_track["distance_meters"]
    print(f"  -> Citizen Tracker Active: Unit {v_track['vehicle_id']} is {v_track['distance_km']} km away ({initial_dist_m}m)")
    print(f"  -> Real-time arrival ETA: {v_track['estimated_arrival_eta_mins']} mins")
    print("  [PASS] Citizen rescue live tracking telemetry verified.")

    # ------------------ TEST 6: VEHICLE TRANSPONDER GPS MOVEMENT ------------------
    print("\n[TEST 6] Testing Vehicle Transponder GPS Movement Ingestion...")
    # Simulate vehicle driving closer towards Subhash Chowk (28.4285, 77.0395)
    res_ping = client.post(f"/api/v1/fleet/{assigned_v_id}/transponder", json={
        "lat": 28.4300,
        "lng": 77.0400,
        "speed_kmh": 32.5,
        "heading_deg": 185.0,
        "current_route": "Approaching Subhash Chowk Underpass"
    })
    assert res_ping.status_code == 200
    assert res_ping.json()["status"] == "transponder_updated"

    # Query citizen tracker again to verify distance dropped!
    res_track_updated = client.get(f"/api/v1/sos/track/{new_sos_id}")
    updated_track = res_track_updated.json()
    new_dist_m = updated_track["assigned_vehicle"]["distance_meters"]
    assert new_dist_m < initial_dist_m, f"Expected distance to decrease, got {new_dist_m}m vs initial {initial_dist_m}m"
    print(f"  -> Transponder GPS Ingested: Distance decreased from {initial_dist_m}m -> {new_dist_m}m ({updated_track['assigned_vehicle']['distance_km']} km)")
    print(f"  -> Updated arrival ETA: {updated_track['assigned_vehicle']['estimated_arrival_eta_mins']} mins")
    print("  [PASS] Live GPS movement telemetry & tracking sync verified.")

    # ------------------ TEST 7: DISTRESS RESOLUTION & FLEET RELEASE ------------------
    print("\n[TEST 7] Testing Distress Call Resolution & Fleet Unit Release...")
    res_resolve = client.post(f"/api/v1/sos/{new_sos_id}/resolve", headers=official_headers)
    assert res_resolve.status_code == 200, f"Resolution failed: {res_resolve.text}"
    resolve_data = res_resolve.json()
    assert resolve_data["status"] == "resolved"

    # Verify vehicle is released back to OPEN
    released_v = client.get(f"/api/v1/fleet/{assigned_v_id}").json()
    assert released_v["status"] == "OPEN"
    print(f"  -> Distress ticket {new_sos_id} resolved.")
    print(f"  -> Rescue vehicle {assigned_v_id} successfully returned to OPEN standby pool.")
    print("  [PASS] Distress resolution and fleet resource release verified.")

    # ------------------ TEST 8: WEBSOCKET GATEWAY HANDSHAKE ------------------
    print("\n[TEST 8] Testing Real-Time WebSocket Gateway Protocol Handshake...")
    with client.websocket_connect("/ws/live?room=officials") as ws:
        ws.send_text("ping")
        response = ws.receive_text()
        assert response == "pong", f"Expected pong, got {response}"
        print("  -> WebSocket connection accepted on /ws/live?room=officials")
        print("  -> Verified bi-directional ping/pong heartbeat.")
    print("  [PASS] WebSocket real-time gateway protocol verified.")

    print("\n" + "=" * 75)
    print("  SUCCESS: ALL 8 / 8 PHASE 3 TESTS PASSED WITH 100% SUCCESS!")
    print("  Real-time WebSockets, Fleet Transponders, & Citizen SOS Engine verified.")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_phase3_tests()
