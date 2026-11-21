"""
JalRakshak NCR - Phase 6 Test Suite: Multi-Agency Disaster Coordination & Official Insurance PDF Generator
Validates:
1. DHBVN 11kV electrical feeder monitoring & flood shock hazard classification.
2. Inter-agency DHBVN power cut request & execution protocol with RBAC.
3. Automated underpass boom barrier monitoring & flood threshold triggers.
4. Remote boom barrier lowering/raising by Traffic Police.
5. Emergency shelter & MLCP multi-level safe dry parking spatial queries.
6. ReportLab official MCG Flood Incident Verification Certificate (PDF) generation.
7. End-to-end municipal audit trail persistence across agencies.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_phase6_multi_agency_coordination():
    print("\n" + "=" * 70)
    print(">>> RUNNING PHASE 6 VERIFICATION TEST SUITE <<<")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: List DHBVN Feeders & Verify Flood Shock Hazard Ratings
    # -------------------------------------------------------------
    print("\n--- TEST 1: Listing DHBVN 11kV Feeders & Shock Hazard Status ---")
    res1 = client.get("/api/v1/agency/dhbvn/feeders")
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.text}"
    feeders = res1.json()
    assert len(feeders) >= 4, f"Expected at least 4 feeders, got {len(feeders)}"

    # Check Hero Honda feeder with 48cm water is CRITICAL_SUBMERGED
    hero_feeder = next((f for f in feeders if f["feeder_code"] == "FDR-HERO-11KV"), None)
    assert hero_feeder is not None, "Hero Honda 11kV feeder not found"
    assert hero_feeder["hazard_status"] == "CRITICAL_SUBMERGED"
    assert hero_feeder["water_depth_near_feeder_cm"] >= 48
    print(f"  [OK] Feeders verified: {len(feeders)} lines active.")
    print(f"  [OK] {hero_feeder['substation_name']}: Depth={hero_feeder['water_depth_near_feeder_cm']}cm -> {hero_feeder['hazard_status']}")

    # -------------------------------------------------------------
    # Step 2: DHBVN Power Cut Request & Execution Lifecycle
    # -------------------------------------------------------------
    print("\n--- TEST 2: DHBVN Power Cut Request, Execution & Restoration ---")
    # Login as MCG Official to request power cut
    client.cookies.clear()
    login_mcg = client.post("/api/v1/auth/official/login", json={
        "identifier": "Vikram Singh",
        "password": "MCG-GURUGRAM-2026"
    })
    assert login_mcg.status_code == 200, f"MCG login failed: {login_mcg.text}"

    # Request power cut
    req_res = client.post("/api/v1/agency/dhbvn/power-cut", json={
        "feeder_id": "FDR-HH-02",
        "water_depth_cm": 52,
        "reason": "Water level surging past transformer plinth level; imminent arc danger."
    })
    assert req_res.status_code == 200, f"Power cut request failed: {req_res.text}"
    req_data = req_res.json()
    assert req_data["power_cut_requested"] is True
    print(f"  [OK] Power cut requested by: {req_data['requested_by']}")

    # Login as DHBVN Engineer to physically execute isolation
    client.cookies.clear()
    login_dhbvn = client.post("/api/v1/auth/official/login", json={
        "identifier": "Rajesh Verma",
        "password": "DHBVN-POWER-2026"
    })
    assert login_dhbvn.status_code == 200, f"DHBVN login failed: {login_dhbvn.text}"

    # Execute cut
    exec_res = client.post("/api/v1/agency/dhbvn/execute", json={
        "feeder_id": "FDR-HH-02"
    })
    assert exec_res.status_code == 200, f"Power cut execution failed: {exec_res.text}"
    exec_data = exec_res.json()
    assert exec_data["power_cut_executed"] is True
    print(f"  [OK] Power cut executed by: {exec_data['executed_by']}")

    # Restore power
    restore_res = client.post("/api/v1/agency/dhbvn/restore", json={
        "feeder_id": "FDR-HH-02"
    })
    assert restore_res.status_code == 200, f"Power restore failed: {restore_res.text}"
    restore_data = restore_res.json()
    assert restore_data["power_restored"] is True
    print(f"  [OK] Power safely restored on FDR-HH-02.")

    # -------------------------------------------------------------
    # Step 3: Underpass Boom Barriers & Automated Trigger Alerts
    # -------------------------------------------------------------
    print("\n--- TEST 3: Boom Barriers Monitoring & Auto-Closure Trigger ---")
    from database import get_db_cursor
    with get_db_cursor(commit=True) as cur:
        cur.execute("UPDATE underpass_barriers SET barrier_state = 'OPEN', closed_by = NULL, closed_at = NULL WHERE id = 'BAR-RAJIV-01';")

    bar_res = client.get("/api/v1/agency/barriers")
    assert bar_res.status_code == 200, f"Barriers list failed: {bar_res.text}"
    barriers = bar_res.json()
    assert len(barriers) >= 3, f"Expected 3 barriers, got {len(barriers)}"

    # Rajiv Chowk barrier with 115cm water should recommend LOWER_BARRIER
    rajiv_bar = next((b for b in barriers if b["id"] == "BAR-RAJIV-01"), None)
    assert rajiv_bar is not None, "Rajiv Chowk boom barrier not found"
    assert rajiv_bar["recommended_action"] == "LOWER_BARRIER", f"Expected LOWER_BARRIER, got {rajiv_bar['recommended_action']}"
    print(f"  [OK] {rajiv_bar['location_name']}: Depth={rajiv_bar['current_water_depth_cm']}cm, Threshold={rajiv_bar['trigger_threshold_cm']}cm -> Recommended: {rajiv_bar['recommended_action']}")

    # -------------------------------------------------------------
    # Step 4: Traffic Police Remote Boom Barrier Operation & RBAC
    # -------------------------------------------------------------
    print("\n--- TEST 4: Traffic Police Remote Barrier Operation & RBAC Check ---")
    # Login as Traffic Police SP
    client.cookies.clear()
    login_police = client.post("/api/v1/auth/official/login", json={
        "identifier": "Amit Dahiya",
        "password": "POLICE-TRAFFIC-2026"
    })
    assert login_police.status_code == 200, f"Traffic police login failed: {login_police.text}"

    # Lower the boom barrier to halt traffic
    close_res = client.post("/api/v1/agency/barriers/BAR-RAJIV-01/toggle", json={
        "state": "CLOSED",
        "reason": "Water depth 115cm. Barrier lowered to prevent vehicle drowning."
    })
    assert close_res.status_code == 200, f"Barrier closure failed: {close_res.text}"
    close_data = close_res.json()
    assert close_data["new_state"] == "CLOSED"
    print(f"  [OK] Boom barrier BAR-RAJIV-01 lowered by {close_data['operated_by']}.")

    # Unauthenticated citizen tries to operate barrier -> should be 401
    client.cookies.clear()
    unauth_bar = client.post("/api/v1/agency/barriers/BAR-RAJIV-01/toggle", json={
        "state": "OPEN"
    })
    assert unauth_bar.status_code == 401, f"Expected 401, got {unauth_bar.status_code}"
    print(f"  [OK] Unauthenticated citizen blocked from operating barriers (401).")

    # -------------------------------------------------------------
    # Step 5: Emergency Shelters & Safe Dry Parking (MLCP) Lookup
    # -------------------------------------------------------------
    print("\n--- TEST 5: Relief Shelters & Safe Dry Parking (MLCP) Query ---")
    # Query all shelters
    shelters_res = client.get("/api/v1/agency/shelters")
    assert shelters_res.status_code == 200, f"Shelters failed: {shelters_res.text}"
    all_shelters = shelters_res.json()
    assert len(all_shelters) >= 5, f"Expected at least 5 shelters, got {len(all_shelters)}"

    # Filter only MLCP Safe Dry Parking Sanctuaries
    mlcp_res = client.get("/api/v1/agency/shelters?shelter_type=MLCP_PARKING")
    assert mlcp_res.status_code == 200
    mlcp_list = mlcp_res.json()
    assert all(s["shelter_type"] == "MLCP_PARKING" for s in mlcp_list)
    assert len(mlcp_list) >= 2
    total_veh_capacity = sum(s["capacity_vehicles"] for s in mlcp_list)
    assert total_veh_capacity >= 4000, f"Expected >4000 vehicle capacity, got {total_veh_capacity}"
    print(f"  [OK] MLCP Multi-Level Dry Parking: {len(mlcp_list)} garages found, total vehicle capacity: {total_veh_capacity} cars.")

    # Spatial nearest test from Medanta Hospital (28.4415, 77.0445)
    near_res = client.get("/api/v1/agency/shelters?lat=28.4415&lng=77.0445&radius_km=10")
    assert near_res.status_code == 200
    near_shelters = near_res.json()
    assert len(near_shelters) > 0
    # First one must be Tau Devi Lal Stadium (~1.0km)
    assert near_shelters[0]["id"] == "SH-01"
    assert near_shelters[0]["distance_km"] < 2.0
    print(f"  [OK] Nearest shelter to Medanta: {near_shelters[0]['name']} ({near_shelters[0]['distance_km']} km away).")

    # -------------------------------------------------------------
    # Step 6: Official Flood Incident Insurance Certificate (PDF)
    # -------------------------------------------------------------
    print("\n--- TEST 6: ReportLab Official Flood Certificate PDF Generation ---")
    cert_payload = {
        "citizen_name": "Kamal Shukla",
        "citizen_phone": "+91-9811223344",
        "vehicle_registration": "HR-26-DK-9012",
        "vehicle_make_model": "Honda City 1.5 i-VTEC (Sedan)",
        "incident_location": "Rajiv Chowk Underpass South Exit (NH-48)",
        "incident_date_time": "20 July 2026, 17:45 HRS IST",
        "flood_water_depth_cm": 115,
        "incident_description": "Vehicle submerged up to window level during sudden cloudburst surcharge at Rajiv Chowk underpass. Engine stalled and hydrolocked.",
        "citizen_aadhaar_last4": "4590",
        "hotspot_id": "hs_rajiv"
    }

    pdf_res = client.post("/api/v1/agency/insurance-certificate", json=cert_payload)
    assert pdf_res.status_code == 200, f"Certificate generation failed: {pdf_res.text}"
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "MCG_Flood_Certificate_HR_26_DK_9012.pdf" in pdf_res.headers.get("content-disposition", "")

    pdf_bytes = pdf_res.content
    assert pdf_bytes.startswith(b"%PDF-"), "PDF does not start with valid PDF magic bytes"
    assert len(pdf_bytes) > 2000, f"PDF too small ({len(pdf_bytes)} bytes)"
    print(f"  [OK] Official Flood Certificate PDF generated successfully: {len(pdf_bytes):,} bytes.")
    print(f"  [OK] Format: PDF-1.4, Header: {pdf_bytes[:8].decode('latin1')}")

    # -------------------------------------------------------------
    # Step 7: Municipal Multi-Agency Audit Trail Persistence
    # -------------------------------------------------------------
    print("\n--- TEST 7: Multi-Agency Audit Trail Persistence ---")
    client.cookies.clear()
    login_admin = client.post("/api/v1/auth/official/login", json={
        "identifier": "Vikram Singh",
        "password": "MCG-GURUGRAM-2026"
    })
    assert login_admin.status_code == 200, f"MCG Official login failed: {login_admin.text}"

    audit_res = client.get("/api/v1/auth/audit-logs")
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]
    actions = [l["action"] for l in logs]
    assert "POWER_CUT_REQUESTED" in actions, "POWER_CUT_REQUESTED not found in audit trail"
    assert "POWER_CUT_EXECUTED" in actions, "POWER_CUT_EXECUTED not found in audit trail"
    assert "BARRIER_STATE_TOGGLED" in actions, "BARRIER_STATE_TOGGLED not found in audit trail"
    print(f"  [OK] Audit trail logged {len(logs)} entries across agencies.")
    print(f"  [OK] Actions verified: POWER_CUT_REQUESTED, POWER_CUT_EXECUTED, BARRIER_STATE_TOGGLED.")

    print("\n" + "=" * 70)
    print(">>> ALL 7 PHASE 6 TESTS PASSED FLAWLESSLY! <<<")
    print("=" * 70)


if __name__ == "__main__":
    test_phase6_multi_agency_coordination()
