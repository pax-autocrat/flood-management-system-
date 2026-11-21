"""
NeerNetra - JalRakshak NCR
Step 2 Automated Verification Suite: 159-Hotspot Drainage Topology Layer & Pareto Engine
Validates:
1. Canonical count: 159 hotspots (36 Tier 1, 83 Tier 2, 40 Tier 3).
2. Geographic integrity: All coordinates strictly within Gurugram bounding box.
3. Pareto 80/20 principle: Top 32 choke points account for 81.0% of systemic risk.
4. Topology endpoints: /api/hotspots/159, /api/hotspots/summary, /api/hotspots/corridors, /api/hotspots/{spot_id}.
5. High-speed batch inference: <20ms execution across all 159 nodes.
6. Pump pre-deployment mitigation effect on individual choke points.
"""

import sys
import os
import time

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from topology_service import topology_service
from main import (
    get_all_hotspots,
    get_topology_summary,
    get_corridors,
    get_hotspot_detail,
    predict_all_hotspots,
    health_check
)

def test_1_canonical_hotspot_counts():
    print("\n[TEST 1] Verifying canonical 159-hotspot tier distribution...")
    all_spots = topology_service.get_all_hotspots()
    assert len(all_spots) == 159, f"Expected 159 hotspots, got {len(all_spots)}"

    t1 = [h for h in all_spots if h["tier"] == 1]
    t2 = [h for h in all_spots if h["tier"] == 2]
    t3 = [h for h in all_spots if h["tier"] == 3]

    assert len(t1) == 36, f"Expected 36 Tier 1 trunk nodes, got {len(t1)}"
    assert len(t2) == 83, f"Expected 83 Tier 2 arterial culverts, got {len(t2)}"
    assert len(t3) == 40, f"Expected 40 Tier 3 ward depressions, got {len(t3)}"

    print(f"  ✓ Total Hotspots: {len(all_spots)}")
    print(f"  ✓ Tier 1 (Trunk Nodes): {len(t1)}")
    print(f"  ✓ Tier 2 (Arterial Culverts): {len(t2)}")
    print(f"  ✓ Tier 3 (Ward Depressions): {len(t3)}")

def test_2_geographic_bounding_box():
    print("\n[TEST 2] Verifying geographic coordinates within Gurugram boundaries...")
    all_spots = topology_service.get_all_hotspots()
    for h in all_spots:
        lat = h["lat"]
        lng = h["lng"]
        elev = h["elevation_m"]
        assert 28.30 <= lat <= 28.55, f"Latitude {lat} out of Gurugram bounds for {h['code']}"
        assert 76.90 <= lng <= 77.20, f"Longitude {lng} out of Gurugram bounds for {h['code']}"
        assert 210.0 <= elev <= 265.0, f"Elevation {elev}m out of realistic Gurugram range for {h['code']}"

    print(f"  ✓ All 159 coordinates verified within Gurugram bounding box (28.30-28.55°N, 76.90-77.20°E).")
    print(f"  ✓ Elevations calibrated between {min(h['elevation_m'] for h in all_spots)}m (sink) and {max(h['elevation_m'] for h in all_spots)}m (Aravalli).")

def test_3_pareto_80_20_principle():
    print("\n[TEST 3] Verifying 80/20 Pareto principle (32 choke points = 81% flood risk)...")
    summary = topology_service.get_summary()
    pareto = summary.get("pareto_principle", {})

    choke_count = pareto.get("critical_choke_point_count")
    choke_pct = pareto.get("critical_choke_point_pct_of_total")
    risk_share = pareto.get("systemic_flood_risk_share_pct")

    assert choke_count == 32, f"Expected 32 choke points, got {choke_count}"
    assert 19.0 <= choke_pct <= 21.0, f"Expected ~20% of total nodes, got {choke_pct}%"
    assert 80.0 <= risk_share <= 82.0, f"Expected ~81% risk share, got {risk_share}%"

    print(f"  ✓ Pareto Choke Points: {choke_count} / 159 nodes ({choke_pct}%)")
    print(f"  ✓ Systemic Flood Accumulation Governed: {risk_share}% (Mathematical Pareto Verified)")

def test_4_topology_api_endpoints():
    print("\n[TEST 4] Testing FastAPI Topology Endpoints...")
    # 1. Health check includes topology metadata
    health = health_check()
    assert health["status"] == "healthy"
    assert health["total_hotspots_indexed"] == 159
    assert "81.0%" in health["pareto_coverage"]

    # 2. Summary
    data = get_topology_summary()
    assert data["total_hotspots"] == 159

    # 3. Corridors
    corridors = get_corridors()["corridors"]
    assert len(corridors) == 3
    leg_ids = [c["id"] for c in corridors]
    assert "LEG_1" in leg_ids and "LEG_2" in leg_ids and "LEG_3" in leg_ids

    # 4. Query all 159
    res_all = get_all_hotspots()
    assert res_all["count"] == 159

    # 5. Filter by Tier 1
    res_t1 = get_all_hotspots(tier=1)
    assert res_t1["count"] == 36

    # 6. Filter by Tier 2
    res_t2 = get_all_hotspots(tier=2)
    assert res_t2["count"] == 83

    # 7. Filter by Tier 3
    res_t3 = get_all_hotspots(tier=3)
    assert res_t3["count"] == 40

    # 8. Filter by Pareto only
    res_pareto = get_all_hotspots(pareto_only=True)
    assert res_pareto["count"] == 32

    # 9. Specific hotspot lookup (Khandsa Box Culvert)
    spot = get_hotspot_detail("GRG-001")
    assert "Khandsa" in spot["name"]
    assert spot["tier"] == 1
    assert spot["is_pareto_choke_point"] is True

    print("  ✓ health_check() -> 159 indexed nodes verified.")
    print("  ✓ get_topology_summary() -> 159 nodes & Pareto summary verified.")
    print("  ✓ get_corridors() -> 3 corridors (Leg 1, Leg 2, Leg 3) verified.")
    print("  ✓ get_all_hotspots() -> 159 items verified.")
    print("  ✓ get_all_hotspots(tier=1) -> 36 items verified.")
    print("  ✓ get_all_hotspots(tier=2) -> 83 items verified.")
    print("  ✓ get_all_hotspots(tier=3) -> 40 items verified.")
    print("  ✓ get_all_hotspots(pareto_only=True) -> 32 choke points verified.")
    print("  ✓ get_hotspot_detail('GRG-001') -> Khandsa Box Culvert verified.")

def test_5_vectorized_batch_prediction_latency():
    print("\n[TEST 5] Testing Vectorized Batch Prediction Latency on all 159 hotspots...")
    # Warmup
    predict_all_hotspots(rain_mm_hr=45.0)

    latencies = []
    for _ in range(10):
        t0 = time.perf_counter()
        data = predict_all_hotspots(rain_mm_hr=50.0)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_ms = sum(latencies) / len(latencies)
    assert data["total_hotspots_evaluated"] == 159
    assert avg_ms < 20.0, f"Expected latency <20ms, got {avg_ms:.2f}ms"

    server_ms = data.get("inference_latency_ms", 0)
    print(f"  ✓ Evaluated all 159 hotspots in: {server_ms} ms (Server ML inference)")
    print(f"  ✓ Execution average over 10 batch runs: {avg_ms:.2f} ms")
    print(f"  ✓ Status Breakdown: {data['status_breakdown']}")

def test_6_pump_mitigation_on_choke_point():
    print("\n[TEST 6] Testing Pump Pre-Deployment Mitigation on Khandsa Box Culvert (GRG-001)...")
    # Without pump
    data_no_pump = predict_all_hotspots(rain_mm_hr=45.0, tier=1)
    spots_no_pump = data_no_pump["hotspots"]
    khandsa_no_pump = next(s for s in spots_no_pump if s["code"] == "GRG-001")
    depth_no_pump = khandsa_no_pump["prediction"]["predicted_depth_cm"]

    # With pump pre-deployed
    data_pump = predict_all_hotspots(rain_mm_hr=45.0, tier=1, pump_active_spot="GRG-001")
    spots_pump = data_pump["hotspots"]
    khandsa_pump = next(s for s in spots_pump if s["code"] == "GRG-001")
    depth_pump = khandsa_pump["prediction"]["predicted_depth_cm"]

    reduction_cm = depth_no_pump - depth_pump
    reduction_pct = (reduction_cm / depth_no_pump) * 100.0

    print(f"  ✓ Khandsa Depth (No Pump): {depth_no_pump} cm")
    print(f"  ✓ Khandsa Depth (With Pump Pre-deployed): {depth_pump} cm")
    print(f"  ✓ Verified Depth Reduction: {reduction_cm:.1f} cm ({reduction_pct:.1f}% mitigation)")
    assert reduction_pct >= 25.0, f"Expected at least 25% depth reduction, got {reduction_pct:.1f}%"

if __name__ == "__main__":
    print("=" * 68)
    print("  NeerNetra | Step 2 Automated Verification Suite")
    print("  Deliverable 1: 159-Hotspot Drainage Topology Layer & Pareto Engine")
    print("=" * 68)

    test_1_canonical_hotspot_counts()
    test_2_geographic_bounding_box()
    test_3_pareto_80_20_principle()
    test_4_topology_api_endpoints()
    test_5_vectorized_batch_prediction_latency()
    test_6_pump_mitigation_on_choke_point()

    print("\n" + "=" * 68)
    print("  ALL 6 STEP 2 TESTS PASSED! (100% SUCCESS)")
    print("=" * 68)
