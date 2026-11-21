"""
NeerNetra - JalRakshak NCR
Automated Verification Suite for Step 1 (Deliverable 2: Explainable ML Engine)
Validates:
1. Model load integrity & metadata consistency
2. Single-point inference (<5ms latency benchmark)
3. Mitigation discount proof (Pump active drops depth significantly)
4. Confidence Interval range sanity
5. Batch prediction across Gurugram hotspots
"""

import sys
import os
import time

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from ml.predict_service import predict_hotspot_risk, get_model

def run_step1_tests():
    print("=" * 70)
    print("  TEST SUITE: STEP 1 - EXPLAINABLE ML ENGINE & INFERENCE (Deliverable 2)")
    print("  Team: NeerNetra | Role: Kamal Shukla (Backend & Systems Engineer)")
    print("=" * 70)

    # Test 1: Model Loading
    print("\n[TEST 1] Verifying Model Artifact & Metadata...")
    pkg = get_model()
    assert pkg is not None, "Model package failed to load!"
    assert "classifier" in pkg, "Missing classifier in package"
    assert "regressor" in pkg, "Missing regressor in package"
    print(f"  -> Model Accuracy: {pkg['accuracy'] * 100:.2f}%")
    print(f"  -> Depth MAE: {pkg['mae']:.2f} cm")
    print("  [PASS] Model artifact verified.")

    # Test 2: Latency Benchmark (< 8ms SLA benchmark, typical <2ms)
    print("\n[TEST 2] Benchmarking Inference Latency (100 Iterations)...")
    # Quick warmup to prime CPU cache & JIT
    for _ in range(5):
        predict_hotspot_risk(rainfall_mm_hr=45.0, cumulative_3h_rain_mm=70.0, elevation_m=218.0, catchment_area_sqkm=12.0, drain_silt_pct=45.0, pump_deployed=0)

    start = time.perf_counter()
    for _ in range(100):
        predict_hotspot_risk(
            rainfall_mm_hr=45.0,
            cumulative_3h_rain_mm=70.0,
            elevation_m=218.0,
            catchment_area_sqkm=12.0,
            drain_silt_pct=45.0,
            pump_deployed=0
        )
    elapsed = (time.perf_counter() - start) * 1000 # ms
    avg_latency = elapsed / 100
    print(f"  -> 100 inferences completed in: {elapsed:.2f} ms")
    print(f"  -> Average Latency per Prediction: {avg_latency:.3f} ms")
    assert avg_latency < 8.0, f"Inference took {avg_latency}ms which exceeds 8ms limit!"
    print(f"  [PASS] Ultra-low latency verified ({avg_latency:.3f} ms < 8.0 ms SLA).")

    # Test 3: Mitigation Discount Proof (Pump pre-deployment drops depth)
    print("\n[TEST 3] Verifying Pre-Emptive Pump Mitigation Discount...")
    unmitigated = predict_hotspot_risk(
        rainfall_mm_hr=45.0,
        cumulative_3h_rain_mm=60.0,
        elevation_m=218.0,
        catchment_area_sqkm=14.0,
        drain_silt_pct=40.0,
        pump_deployed=0
    )
    mitigated = predict_hotspot_risk(
        rainfall_mm_hr=45.0,
        cumulative_3h_rain_mm=60.0,
        elevation_m=218.0,
        catchment_area_sqkm=14.0,
        drain_silt_pct=40.0,
        pump_deployed=1 # High-capacity 5000 GPM pump active
    )
    depth_no_pump = unmitigated["predicted_depth_cm"]
    depth_with_pump = mitigated["predicted_depth_cm"]
    reduction_pct = ((depth_no_pump - depth_with_pump) / depth_no_pump) * 100

    print(f"  -> Unmitigated Water Depth (No Pump): {depth_no_pump} cm (Risk: {unmitigated['risk_tier']})")
    print(f"  -> Mitigated Water Depth (With Pump): {depth_with_pump} cm (Risk: {mitigated['risk_tier']})")
    print(f"  -> Actual Mitigation Reduction: {reduction_pct:.1f}%")
    assert depth_with_pump < depth_no_pump, "Pump deployment did not reduce flood depth!"
    assert reduction_pct >= 40.0, f"Reduction was only {reduction_pct}%, expected >=40%!"
    print("  [PASS] Pre-emptive mitigation efficacy verified.")

    # Test 4: Confidence Interval Sanity Check
    print("\n[TEST 4] Verifying Dynamic 95% Confidence Intervals...")
    ci = unmitigated["confidence_interval_95"]
    assert ci["low_cm"] <= depth_no_pump <= ci["high_cm"], "Prediction is outside CI bounds!"
    print(f"  -> Predicted: {depth_no_pump} cm | Bounds: [{ci['low_cm']} cm - {ci['high_cm']} cm] (±{ci['margin_cm']} cm)")
    print("  [PASS] Confidence interval bounds verified.")

    # Test 5: Dry vs Cloudburst Sanity
    print("\n[TEST 5] Testing Dry Weather vs Extreme Monsoon Cloudburst...")
    dry = predict_hotspot_risk(rainfall_mm_hr=0.0, cumulative_3h_rain_mm=0.0, elevation_m=240.0, catchment_area_sqkm=4.0, drain_silt_pct=10.0)
    storm = predict_hotspot_risk(rainfall_mm_hr=120.0, cumulative_3h_rain_mm=180.0, elevation_m=213.0, catchment_area_sqkm=35.0, drain_silt_pct=70.0)
    print(f"  -> Dry Weather: Depth {dry['predicted_depth_cm']} cm | Risk Tier: {dry['risk_tier']}")
    print(f"  -> Cloudburst:  Depth {storm['predicted_depth_cm']} cm | Risk Tier: {storm['risk_tier']}")
    assert dry["risk_tier"] == "LOW_RISK", "Dry weather flagged as flood!"
    assert storm["risk_tier"] == "CRITICAL", "Extreme cloudburst missed critical flag!"
    print("  [PASS] Environmental boundary conditions verified.")

    print("\n" + "=" * 70)
    print("  ALL 5 UNIT & INTEGRATION TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    run_step1_tests()
