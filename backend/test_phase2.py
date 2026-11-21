"""
JalRakshak NCR — Phase 2 Automated Verification Suite
Validates:
1. Persistent Hotspot Telemetry & Passability Calculation
2. Road Safety Percentage City-Wide Metric
3. Dynamic Mitigation Math (Drain Cleaned -40%, Pump Active -65%)
4. Master 36 Stormwater Drains Registry (Leg 1, Leg 2, Leg 3)
5. Contractor Desilting Audit Logging & Photographic Proof
6. Live Weather Ingestion & Scenario Presets (Normal, AI, Storm)
7. 24-Hour Rainfall Accumulation Curve & Doppler Radar Reflectivity
8. Strict RBAC Enforcement on Civic Infrastructure Mutation Endpoints
"""

import sys
import os
from fastapi.testclient import TestClient

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from main import app
from services.auth_service import auth_service

client = TestClient(app)

def run_phase2_tests():
    print("=" * 75)
    print("  PHASE 2 VERIFICATION: HOTSPOTS TELEMETRY, 36 DRAINS & WEATHER ENGINE")
    print("  Team: NeerNetra | Lead: Kamal Shukla | SustainX 2026")
    print("=" * 75)

    # 0. Setup Tokens for RBAC testing
    official_user = auth_service.authenticate_official("Vikram Singh", "MCG-GURUGRAM-2026")
    official_token = auth_service.create_access_token({
        "sub": official_user["id"],
        "name": official_user["name"],
        "role": official_user["role"],
        "agency": official_user.get("agency_code")
    })
    official_headers = {"Authorization": f"Bearer {official_token}"}

    citizen_user = auth_service.get_or_create_citizen("+91-9811046021", "Aarav Sharma")
    citizen_token = auth_service.create_access_token({
        "sub": citizen_user["id"],
        "name": citizen_user["name"],
        "role": citizen_user["role"]
    })
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # ------------------ TEST 1: HOTSPOTS TELEMETRY & PASSABILITY ------------------
    print("\n[TEST 1] Testing Persistent Hotspots Telemetry & Status Badges...")
    res_spots = client.get("/api/v1/hotspots")
    assert res_spots.status_code == 200
    spots_data = res_spots.json()
    assert spots_data["count"] == 8, f"Expected 8 primary arterial spots, got {spots_data['count']}"
    
    # Check Rajiv Chowk baseline
    rajiv = next(s for s in spots_data["hotspots"] if s["id"] == "hs_rajiv")
    assert rajiv["status"] == "FLOODED"
    print(f"  -> Rajiv Chowk Baseline Depth: {rajiv['effective_depth_cm']} cm (Status: {rajiv['status']})")
    print("  [PASS] Hotspots telemetry & passability calculation verified.")

    # ------------------ TEST 2: ROAD SAFETY PERCENTAGE CALCULATION ------------------
    print("\n[TEST 2] Testing City-Wide Road Safety Percentage Calculation...")
    res_safety = client.get("/api/v1/hotspots/road-safety")
    assert res_safety.status_code == 200
    safety_data = res_safety.json()
    assert "road_safety_pct" in safety_data
    assert "breakdown" in safety_data
    pct = safety_data["road_safety_pct"]
    print(f"  -> Storm Road Safety Metric: {pct}% Safe Passability")
    print(f"  -> Spot Breakdown: {safety_data['breakdown']}")
    print(f"  -> Advisory: {safety_data['advisory']}")
    print("  [PASS] Municipal Road Safety Percentage verified.")

    # ------------------ TEST 3: DRAIN DESILTING & PUMP MITIGATION MATH ------------------
    print("\n[TEST 3] Testing Dynamic Mitigation Math (Drain -40%, Pump -65%)...")
    # 3A. Toggle Drain Cleaned
    res_drain_toggle = client.post("/api/v1/hotspots/hs_rajiv/toggle-drain", headers=official_headers)
    assert res_drain_toggle.status_code == 200
    rajiv_cleaned = res_drain_toggle.json()["hotspot"]
    assert rajiv_cleaned["drain_cleaned"] == 1
    # 115 * 0.60 = 69 cm
    assert rajiv_cleaned["effective_depth_cm"] == 69, f"Expected 69cm after desilting, got {rajiv_cleaned['effective_depth_cm']}"
    print(f"  -> Desilted Rajiv Chowk Drain: Depth dropped 115cm -> {rajiv_cleaned['effective_depth_cm']}cm (-40%)")

    # 3B. Toggle Pump Assigned
    res_pump_toggle = client.post("/api/v1/hotspots/hs_rajiv/toggle-pump", headers=official_headers)
    assert res_pump_toggle.status_code == 200
    rajiv_pumped = res_pump_toggle.json()["hotspot"]
    assert rajiv_pumped["pump_assigned"] == 1
    # 115 * 0.60 * 0.35 = 24 cm (< 25cm -> Becomes CLEAR / SAFE!)
    assert rajiv_pumped["effective_depth_cm"] == 24, f"Expected 24cm with pump, got {rajiv_pumped['effective_depth_cm']}"
    assert rajiv_pumped["status"] == "CLEAR"
    print(f"  -> Assigned 5000 GPM Pump: Depth dropped to {rajiv_pumped['effective_depth_cm']}cm (Status changed to CLEAR!)")

    # Reset Rajiv Chowk back
    client.post("/api/v1/hotspots/hs_rajiv/toggle-drain", json={"active": False}, headers=official_headers)
    client.post("/api/v1/hotspots/hs_rajiv/toggle-pump", json={"active": False}, headers=official_headers)
    print("  [PASS] Mitigation discount mathematical proof verified.")

    # ------------------ TEST 4: MASTER 36 STORMWATER DRAINS REGISTRY ------------------
    print("\n[TEST 4] Testing Master 36 Stormwater Drains Registry (Leg 1, Leg 2, Leg 3)...")
    res_drains = client.get("/api/v1/drains")
    assert res_drains.status_code == 200
    drains_data = res_drains.json()
    assert drains_data["total_master_drains"] == 36
    assert drains_data["count"] == 36, f"Expected 36 drains, got {drains_data['count']}"

    # Verify Corridor Breakdown
    leg1 = [d for d in drains_data["drains"] if "LEG 1" in d["catchment_leg"]]
    leg2 = [d for d in drains_data["drains"] if "LEG 2" in d["catchment_leg"]]
    leg3 = [d for d in drains_data["drains"] if "LEG 3" in d["catchment_leg"]]
    assert len(leg1) == 12, f"Leg 1 count {len(leg1)} != 12"
    assert len(leg2) == 12, f"Leg 2 count {len(leg2)} != 12"
    assert len(leg3) == 12, f"Leg 3 count {len(leg3)} != 12"
    print(f"  -> Total Master Drains: {drains_data['count']} (Leg 1: 12, Leg 2: 12, Leg 3: 12)")

    # Test Drain Summary
    res_drain_sum = client.get("/api/v1/drains/summary")
    assert res_drain_sum.status_code == 200
    sum_data = res_drain_sum.json()
    assert "city_desilting_percentage" in sum_data
    assert "total_dredged_volume_m3" in sum_data
    print(f"  -> City Desilting Progress: {sum_data['city_desilting_percentage']}% ({sum_data['cleaned_or_verified_count']}/36 Drains Cleaned)")
    print(f"  -> Total Dredged Silt Volume: {sum_data['total_dredged_volume_m3']} m³")
    print("  [PASS] Master 36 stormwater drains registry verified.")

    # ------------------ TEST 5: CONTRACTOR DESILTING AUDIT & PHOTO PROOFS ------------------
    print("\n[TEST 5] Testing Contractor Desilting Audit & Photographic Proof Logging...")
    res_audit = client.post("/api/v1/drains/DR-25/audit", json={
        "contractor_name": "Haryana Drainage Consortium",
        "dredged_volume_m3": 450.0,
        "photo_before_url": "https://s3.jalrakshak.in/proofs/DR25_before.jpg",
        "photo_after_url": "https://s3.jalrakshak.in/proofs/DR25_after.jpg",
        "notes": "Khandsa culvert bottleneck dredged by 450 m3 silt; silt hauled to disposal yard."
    }, headers=official_headers)
    assert res_audit.status_code == 200, f"Audit logging failed: {res_audit.text}"
    audit_data = res_audit.json()
    assert audit_data["status"] == "audit_logged"
    assert audit_data["status_set_to"] == "CLEANED"
    print(f"  -> Audit Record Generated: ID {audit_data['audit_id'][:8]}...")
    print(f"  -> Drain DR-25 (Khandsa Box Culvert) marked as CLEANED.")

    # Verify audit is queryable in drain detail
    res_detail = client.get("/api/v1/drains/DR-25")
    assert res_detail.status_code == 200
    assert len(res_detail.json()["audit_logs"]) >= 1
    print("  [PASS] Contractor desilting audit & photo verification verified.")

    # ------------------ TEST 6: LIVE WEATHER TELEMETRY & PRESETS ------------------
    print("\n[TEST 6] Testing Live Weather Engine Telemetry & Scenario Switching...")
    res_w_curr = client.get("/api/v1/weather/current")
    assert res_w_curr.status_code == 200
    w_curr = res_w_curr.json()
    assert "precipitation_mm_hr" in w_curr
    assert "station" in w_curr
    print(f"  -> Active Weather: {w_curr['temperature_c']}°C | Rain: {w_curr['precipitation_mm_hr']} mm/hr ({w_curr['alert_level']})")

    # Test Scenario Switching
    res_w_ai = client.post("/api/v1/weather/scenario", json={"scenario": "ai"})
    assert res_w_ai.status_code == 200
    assert res_w_ai.json()["precipitation_mm_hr"] == 65.0
    print("  -> Switched to Scenario 'AI': 65 mm/hr Downpour")

    res_w_norm = client.post("/api/v1/weather/scenario", json={"scenario": "normal"})
    assert res_w_norm.status_code == 200
    assert res_w_norm.json()["precipitation_mm_hr"] == 18.0
    print("  -> Switched to Scenario 'Normal': 18 mm/hr Light Rain")

    # Reset back to storm
    client.post("/api/v1/weather/scenario", json={"scenario": "storm"})
    print("  [PASS] Weather station presets & scenario switching verified.")

    # ------------------ TEST 7: 24-HOUR ACCUMULATION & RADAR REFLECTIVITY ------------------
    print("\n[TEST 7] Testing 24-Hour Accumulation Curve & Doppler Radar Loop...")
    res_accum = client.get("/api/v1/weather/accumulation")
    assert res_accum.status_code == 200
    accum_data = res_accum.json()
    assert len(accum_data["curve_points"]) == 24
    print(f"  -> 24-Hour Total Rainfall Accumulation: {accum_data['total_24h_accumulation_mm']} mm (24 Data Points)")

    res_radar = client.get("/api/v1/weather/radar")
    assert res_radar.status_code == 200
    radar_data = res_radar.json()
    assert len(radar_data["frames"]) == 6
    print(f"  -> Doppler Radar Frames Generated: {len(radar_data['frames'])} S-Band Frames ({radar_data['radar_station']})")
    print("  [PASS] 24-Hour accumulation curve & Doppler radar metadata verified.")

    # ------------------ TEST 8: RBAC PROTECTION ON INFRASTRUCTURE ENDPOINTS ------------------
    print("\n[TEST 8] Testing RBAC Protection on Infrastructure Endpoints...")
    # Citizen attempts to update telemetry -> MUST RETURN 403
    res_cit_telemetry = client.patch("/api/v1/hotspots/hs_rajiv/telemetry", json={"depth_cm": 150}, headers=citizen_headers)
    assert res_cit_telemetry.status_code == 403, f"Expected 403 for Citizen, got {res_cit_telemetry.status_code}"

    # Citizen attempts to update drain status -> MUST RETURN 403
    res_cit_drain = client.patch("/api/v1/drains/DR-01/status", json={"status": "CLEANED"}, headers=citizen_headers)
    assert res_cit_drain.status_code == 403, f"Expected 403 for Citizen, got {res_cit_drain.status_code}"
    print("  -> Confirmed: Civilians strictly blocked with 403 Forbidden on infrastructure mutations.")
    print("  [PASS] RBAC protection on Phase 2 endpoints verified.")

    print("\n" + "=" * 75)
    print("  SUCCESS: ALL 8 / 8 PHASE 2 TESTS PASSED WITH 100% SUCCESS!")
    print("  Hotspots telemetry, Master 36 Drains, & Live Weather Engine verified.")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_phase2_tests()
