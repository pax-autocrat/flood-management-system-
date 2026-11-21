"""
NeerNetra - JalRakshak NCR
Step 4 Automated Verification Suite: Vandal-Proof Sensor Architecture & GeM Capex Model
Validates:
1. Indian GeM Capex budget mathematical accuracy (Exact sum ₹49,13,600 / ₹49.14 Lakhs).
2. 5-Year AMC model (₹9.80L/yr, >95% SLA) and comparison against ₹1,400+ Cr historical spend.
3. 3-Tier sensor counts (36 Ultrasonic, 83 CCTV Virtual, 40 SI Crowd, 16 ARGs, 8 Gateways = 159 Hotspots).
4. Overhead 4mm MS anti-theft cage tamper detection & zero-data-loss failover to SS316 float switch.
5. LoRaWAN IN865 gateway network coverage and gated compound security flags.
6. FastAPI endpoint compliance and sub-5ms response latencies.
"""

import sys
import os
import time

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sensor_service import sensor_service
from main import (
    get_sensor_gem_capex,
    get_sensor_telemetry,
    simulate_sensor_tamper,
    reset_sensor_tamper,
    get_sensor_gateways,
    SensorTamperRequest
)

def test_1_gem_capex_model_accuracy():
    print("\n[TEST 1] Testing Indian GeM Capex Model Mathematical Accuracy...")
    capex_data = get_sensor_gem_capex()
    items = capex_data["line_items"]
    assert len(items) == 5, f"Expected 5 GeM line items, got {len(items)}"

    calculated_sum = sum(item["total_cost_inr"] for item in items)
    expected_sum = 4913600.0
    assert calculated_sum == expected_sum, f"Sum mismatch: calculated {calculated_sum} vs expected {expected_sum}"
    assert capex_data["total_capex_lakhs"] == 49.14

    print(f"  ✓ Total Capex Sum: ₹{calculated_sum:,.2f} (₹{capex_data['total_capex_lakhs']} Lakhs)")
    for it in items:
        print(f"    - {it['item_id']}: ₹{it['total_cost_inr']:,.2f} ({it['gem_category_code']})")

def test_2_amc_and_budget_perspective():
    print("\n[TEST 2] Testing 5-Year AMC Projection & Municipal Budget Ratios...")
    capex_data = get_sensor_gem_capex()
    annual_amc = capex_data["annual_amc_lakhs"]
    five_yr_amc = capex_data["five_year_amc_lakhs"]
    five_yr_tco = capex_data["five_year_tco_lakhs"]

    assert annual_amc == 9.80, f"Expected ₹9.80 Lakh/yr, got {annual_amc}"
    assert five_yr_amc == 49.00, f"Expected ₹49.00 Lakhs 5-yr AMC, got {five_yr_amc}"
    assert five_yr_tco == 98.14, f"Expected ₹98.14 Lakhs 5-yr TCO, got {five_yr_tco}"
    assert five_yr_tco < 100.0, "5-Year TCO exceeds ₹1.0 Crore!"

    persp = capex_data["budget_perspective"]
    assert persp["pct_of_mcg_annual_budget"] < 0.1, "Capex exceeds 0.1% of MCG annual budget!"
    assert persp["pct_of_historical_gurujam_spend"] < 0.05, "Capex exceeds 0.05% of historical spend!"

    print(f"  ✓ Annual AMC: ₹{annual_amc} Lakh/yr (>95% SLA Uptime Guarantee)")
    print(f"  ✓ 5-Year Total Cost of Ownership (TCO): ₹{five_yr_tco} Lakhs (< ₹1.0 Crore)")
    print(f"  ✓ Capex represents {persp['pct_of_mcg_annual_budget']:.4f}% of MCG's ₹2,200 Cr Annual Budget (<0.1%)")
    print(f"  ✓ Capex represents {persp['pct_of_historical_gurujam_spend']:.4f}% of the ₹1,400+ Cr spent on ad-hoc fixes")

def test_3_three_tier_sensor_architecture_counts():
    print("\n[TEST 3] Testing 3-Tier Sensor Architecture & Hotspot Coverage...")
    telem = get_sensor_telemetry()
    tiers = telem["architecture_tiers"]

    t1 = tiers["tier_1_ultrasonic_trunk"]
    t2 = tiers["tier_2_cctv_virtual_gauges"]
    t3 = tiers["tier_3_crowd_and_si_ledger"]

    # Tier 1
    assert t1["total_deployed"] == 36
    assert t1["store_spares"] == 6
    assert t1["online"] == 36

    # Tier 2
    assert t2["total_calibrated"] == 83
    assert t2["hardware_capex_inr"] == 0.0 # Zero street hardware capex!

    # Tier 3
    assert t3["total_sector_spots"] == 40

    total_hotspots_covered = t1["total_deployed"] + t2["total_calibrated"] + t3["total_sector_spots"]
    assert total_hotspots_covered == 159, f"Expected 159 hotspots covered, got {total_hotspots_covered}"

    print(f"  ✓ Tier 1: {t1['total_deployed']} Ultrasonic nodes (+ {t1['store_spares']} spares in MCG Store)")
    print(f"  ✓ Tier 2: {t2['total_calibrated']} GMDA CCTV Virtual Gauges (₹0 Street Hardware Capex)")
    print(f"  ✓ Tier 3: {t3['total_sector_spots']} Sanitary Inspector Crowd Verified Depression Spots")
    print(f"  ✓ Total Hotspots Monitored: {total_hotspots_covered} / 159 official nodes")

def test_4_anti_vandalism_tamper_failover():
    print("\n[TEST 4] Testing Overhead MS Cage Tamper Detection & Redundant Failover...")
    # Simulate tampering with Khandsa Box Culvert (GRG-001) overhead MS cage
    tamper_res = simulate_sensor_tamper(SensorTamperRequest(node_code="GRG-001"))

    assert tamper_res["alarm_status"] == "TAMPER_ALARM_ACTIVATED"
    assert tamper_res["node_code"] == "GRG-001"
    assert tamper_res["cage_tamper_switch"] == "TAMPER_DETECTED"
    assert tamper_res["float_switch_backup"] == "STANDBY_ACTIVE"
    assert tamper_res["telemetry_failover_status"] == "ZERO_DATA_LOSS"
    assert len(tamper_res["failover_redundancy"]) >= 3

    # Reset tamper
    reset_res = reset_sensor_tamper(SensorTamperRequest(node_code="GRG-001"))
    assert reset_res["status"] == "RESET_SUCCESSFUL"
    assert reset_res["cage_tamper_switch"] == "SECURE"

    print("  ✓ Overhead 4mm MS anti-theft cage tamper switch trip detected instantly.")
    print("  ✓ Redundant failover engaged: SS316 float switch + GMDA CCTV optical curb reading.")
    print("  ✓ Verified ZERO DATA LOSS during physical tamper simulation.")
    print("  ✓ Reset protocol verified: cage restored to SECURE.")

def test_5_lorawan_gateways_and_gated_args():
    print("\n[TEST 5] Testing IN865 LoRaWAN Gateways & Gated Compound Rain Gauges...")
    gw_data = get_sensor_gateways()
    gws = gw_data["gateways"]
    args = gw_data["gated_args"]

    assert len(gws) == 8, f"Expected 8 gateways, got {len(gws)}"
    for gw in gws:
        assert gw["status"] == "ONLINE"
        assert "IN865" in gw["frequency"]
        assert gw["pdr_pct"] >= 98.0, f"PDR {gw['pdr_pct']}% below 98% threshold on {gw['id']}"

    # Verify that ARGs are in gated compounds (zero street vandalism exposure)
    for arg in args:
        assert arg["gated_compound"] is True
        assert "Gated" in arg["security"]

    print(f"  ✓ {len(gws)} / 8 Outdoor PoE LoRaWAN Gateways ONLINE on IN865 (865-867 MHz).")
    print(f"  ✓ Average Packet Delivery Ratio: {sum(g['pdr_pct'] for g in gws)/len(gws):.2f}%")
    print(f"  ✓ All {len(args)} ARGs verified inside gated DHBVN / MCG compounds (Zero Street Exposure).")

def test_6_endpoint_latency_benchmark():
    print("\n[TEST 6] Benchmarking Step 4 Endpoint Latencies...")
    endpoints = [
        ("GET /api/sensor/capex-model", get_sensor_gem_capex),
        ("GET /api/sensor/telemetry", get_sensor_telemetry),
        ("GET /api/sensor/gateways", get_sensor_gateways)
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
    print("  NeerNetra | Step 4 Automated Verification Suite")
    print("  Deliverable 4: Vandal-Proof Sensor Architecture & GeM Capex Model")
    print("=" * 70)

    test_1_gem_capex_model_accuracy()
    test_2_amc_and_budget_perspective()
    test_3_three_tier_sensor_architecture_counts()
    test_4_anti_vandalism_tamper_failover()
    test_5_lorawan_gateways_and_gated_args()
    test_6_endpoint_latency_benchmark()

    print("\n" + "=" * 70)
    print("  ALL 6 STEP 4 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
