"""
NeerNetra - JalRakshak NCR
Step 3 Automated Verification Suite: MCG Pre-Event SOP Engine & Public Commitment View
Validates:
1. 4-Stage SOP protocol state engine (T-24H, T-12H, T-6H, T-2H) and meteorological threshold auto-triggers.
2. Field engineer digital check-off and signoff verification.
3. Public Commitment Board cryptographic integrity (HMAC-SHA256 tamper-proof detection).
4. Algorithmic RWA Geofence Lock: Rejection of Ring-A trunk diversion and auto-rerouting to Ring-B.
5. Commissioner Dual-Key Override protocol with public RTI audit logging.
6. Zero-lag bilingual (Hindi + English) WhatsApp work order dispatch payloads.
7. FastAPI endpoint compliance and response latency.
"""

import sys
import os
import time

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sop_service import sop_service
from main import (
    get_sop_status,
    checkoff_sop_task,
    auto_trigger_sop,
    get_whatsapp_work_order,
    get_public_commitment_board,
    log_public_commitment,
    get_fleet_telematics,
    dispatch_fleet_vehicle,
    issue_dual_key_override,
    SopCheckoffRequest,
    AutoTriggerRequest,
    FleetDispatchRequest,
    DualKeyOverrideRequest,
    PublicCommitmentRequest
)

def test_1_sop_state_engine_and_triggers():
    print("\n[TEST 1] Testing 4-Phase Pre-Event SOP Protocol & Meteorological Triggers...")
    status = get_sop_status()
    phases = status["phases"]
    assert len(phases) == 4, f"Expected 4 SOP phases, got {len(phases)}"

    phase_codes = [p["phase_code"] for p in phases]
    assert phase_codes == ["T-24H", "T-12H", "T-6H", "T-2H"]

    # Test rain threshold auto-trigger
    # Triggering with 38 mm/hr should complete T-24H (15mm), T-12H (25mm), and T-6H (35mm)
    trig_res = auto_trigger_sop(AutoTriggerRequest(rain_mm_hr=38.0))
    updated_status = get_sop_status()
    completed_codes = [p["phase_code"] for p in updated_status["phases"] if p["completed"]]

    assert "T-24H" in completed_codes
    assert "T-12H" in completed_codes
    assert "T-6H" in completed_codes
    assert "T-2H" not in completed_codes # 38mm < 50mm trigger

    print(f"  ✓ 4 SOP Phases verified: {phase_codes}")
    print(f"  ✓ Auto-trigger at 38 mm/hr successfully activated: {completed_codes}")
    print(f"  ✓ Overall completion rate: {updated_status['overall_completion_pct']}%")

def test_2_field_checkoff_signoff():
    print("\n[TEST 2] Testing Field Engineer Digital Checkoff & Verification...")
    res = checkoff_sop_task(SopCheckoffRequest(
        sop_id="SOP-2H",
        verified_by="TI-Traffic-1095 (Gurugram Police)",
        notes="Boom barriers lowered at Rajiv Chowk Underpass. Diversion to Golf Course Rd active."
    ))

    assert res["status"] == "success"
    assert res["phase"] == "T-2 HOURS (NOWCAST CLOUDBURST)"
    assert res["verified_by"] == "TI-Traffic-1095 (Gurugram Police)"

    status = get_sop_status()
    p2h = next(p for p in status["phases"] if p["phase_code"] == "T-2H")
    assert p2h["completed"] is True
    assert p2h["notes"] is not None

    print(f"  ✓ Digital signoff recorded for SOP-2H by: {res['verified_by']}")
    print(f"  ✓ Timestamp recorded: {res['completed_at']}")

def test_3_public_commitment_board_hmac_integrity():
    print("\n[TEST 3] Testing Public Commitment Board HMAC-SHA256 Cryptographic Integrity...")
    board_data = get_public_commitment_board()
    entries = board_data["entries"]
    assert len(entries) >= 2

    # Verify all current entries carry valid HMAC signatures
    for e in entries:
        assert e["signature_valid"] is True, f"Tampered signature detected on {e['id']}"
        assert e["audit_verification"] == "TAMPER-PROOF CRYPTOGRAPHIC PROOF VERIFIED"

    # Test Tamper Detection: Altering depth or location should invalidate the cryptographic signature
    test_entry = entries[0]
    tampered_sig = sop_service._compute_signature(
        test_entry["id"],
        test_entry["predicted_unmitigated_depth_cm"] + 50.0, # Tampered depth
        test_entry["actual_held_depth_cm"],
        test_entry["location_name"]
    )
    assert tampered_sig != test_entry["digital_signature_hmac"], "HMAC collision or failed tamper detection!"

    print(f"  ✓ Verified {len(entries)} Public Commitment Board ledger items.")
    print("  ✓ Cryptographic HMAC-SHA256 proof verified: zero tampering detected.")
    print("  ✓ Tamper detection check confirmed: altered data mathematically invalidates seal.")

def test_4_algorithmic_rwa_geofence_lock():
    print("\n[TEST 4] Testing Algorithmic RWA Geofence Lock (Ring-A Trunk vs Ring-B Flex)...")
    # 1. Attempt unauthorized diversion of Ring-A trunk-locked Super Sucker
    rwa_attempt = dispatch_fleet_vehicle(FleetDispatchRequest(
        vehicle_id="TANKER-101",
        target_location="Sector 42 Posh Colony Internal Puddle",
        requestor="Influential RWA President / Councillor",
        is_vip_request=True
    ))

    assert rwa_attempt["dispatch_status"] == "REJECTED_BY_ALGORITHMIC_GEOFENCE"
    assert rwa_attempt["ring"] == "RING-A"
    assert "QRV" in rwa_attempt["ring_b_substitute_dispatched"]
    print("  ✓ Ring-A Diversion Request REJECTED by algorithmic geofence lock.")
    print(f"  ✓ Automated countermeasure: Substituted with {rwa_attempt['ring_b_substitute_dispatched']}.")

    # 2. Legitimate trunk dispatch of Ring-A to a choke point should SUCCEED
    trunk_dispatch = dispatch_fleet_vehicle(FleetDispatchRequest(
        vehicle_id="TANKER-101",
        target_location="GRG-001 (Khandsa Box Culvert Trunk Sump)",
        requestor="MCG Central Control Room"
    ))
    assert trunk_dispatch["dispatch_status"] == "APPROVED"
    assert trunk_dispatch["billing_active"] is True
    print("  ✓ Ring-A Authorized Trunk Dispatch APPROVED for Khandsa Box Culvert.")

    # 3. Ring-B unit dispatch to colony internal roads should SUCCEED freely
    ring_b_dispatch = dispatch_fleet_vehicle(FleetDispatchRequest(
        vehicle_id="QRV-401",
        target_location="Sector 42 Internal Road Puddle",
        requestor="RWA Resident Request"
    ))
    assert ring_b_dispatch["dispatch_status"] == "APPROVED"
    assert ring_b_dispatch["ring"] == "RING-B"
    print("  ✓ Ring-B Ward & RWA Buffer Dispatch APPROVED without restriction.")

def test_5_commissioner_dual_key_override():
    print("\n[TEST 5] Testing Commissioner Dual-Key Override Protocol...")
    # Issue override token
    token_rec = issue_dual_key_override(DualKeyOverrideRequest(
        reason="Hospital emergency approach road clearance outside Medanta",
        authorized_by="Municipal Commissioner MCG"
    ))
    token = token_rec["token"]
    assert "RTI-2026-DK-" in token

    # Attempt Ring-A diversion WITH the valid token
    override_dispatch = dispatch_fleet_vehicle(FleetDispatchRequest(
        vehicle_id="TANKER-102",
        target_location="Sector 38 Colony Backroad (Near Medanta)",
        requestor="Emergency Medical Incident Commander",
        override_token=token
    ))

    assert override_dispatch["dispatch_status"] == "APPROVED_UNDER_OVERRIDE"
    assert override_dispatch["override_used"] is True
    assert override_dispatch["commissioner_token"] == token
    assert "COMMISSIONER DUAL-KEY AUTHORIZED" in override_dispatch["rti_audit_log"]

    # Verify that the override is logged in the public commitment ledger for RTI transparency
    ledger_entries = get_public_commitment_board()["entries"]
    override_entry = next((e for e in ledger_entries if token in e["staged_asset"]), None)
    assert override_entry is not None
    assert override_entry["signature_valid"] is True

    print(f"  ✓ Dual-Key Token Generated: {token}")
    print("  ✓ Ring-A Diversion APPROVED under Dual-Key Override.")
    print(f"  ✓ Public RTI Ledger Entry Created & Digitally Signed: {override_entry['id']}")

def test_6_bilingual_whatsapp_payload():
    print("\n[TEST 6] Testing Bilingual (Hindi + English) WhatsApp Work Orders...")
    payload = get_whatsapp_work_order("SOP-12H")

    assert payload["sop_id"] == "SOP-12H"
    assert payload["phase"] == "T-12H"
    assert "+91" in payload["recipient_je_phone"]
    assert "HERO HONDA" in payload["english_message"].upper() or "GRG-002" in payload["english_message"]
    assert "हीरो होंडा" in payload["hindi_message"] # Hindi script verified

    print(f"  ✓ English Work Order: {payload['english_message'].splitlines()[0]}")
    print(f"  ✓ Hindi Work Order: {payload['hindi_message']}")
    print(f"  ✓ WhatsApp 1-Click Link: {payload['formatted_whatsapp_url'][:65]}...")

def test_7_endpoint_latency_benchmark():
    print("\n[TEST 7] Benchmarking Step 3 Endpoint Latencies...")
    endpoints = [
        ("GET /api/sop/status", get_sop_status),
        ("GET /api/sop/public-commitment-board", get_public_commitment_board),
        ("GET /api/fleet/status", get_fleet_telematics)
    ]

    for name, fn in endpoints:
        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
        avg = sum(times) / len(times)
        assert avg < 5.0, f"Latency {avg:.2f}ms exceeds 5.0ms SLA for {name}"
        print(f"  ✓ {name}: {avg:.3f} ms average latency (< 5.0 ms SLA)")

if __name__ == "__main__":
    print("=" * 70)
    print("  NeerNetra | Step 3 Automated Verification Suite")
    print("  Deliverable 3: MCG Pre-Event SOP Engine & Public Commitment View")
    print("=" * 70)

    test_1_sop_state_engine_and_triggers()
    test_2_field_checkoff_signoff()
    test_3_public_commitment_board_hmac_integrity()
    test_4_algorithmic_rwa_geofence_lock()
    test_5_commissioner_dual_key_override()
    test_6_bilingual_whatsapp_payload()
    test_7_endpoint_latency_benchmark()

    print("\n" + "=" * 70)
    print("  ALL 7 STEP 3 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
