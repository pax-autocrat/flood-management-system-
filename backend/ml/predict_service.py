"""
NeerNetra - JalRakshak NCR
High-Performance ML Inference Service (Deliverable 2)
Sub-millisecond inference service for real-time flood prediction and confidence interval estimation.
"""

import os
import json
from typing import Optional, List, Dict, Any, Set
import joblib
import numpy as np

curr_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(curr_dir, "models", "flood_model.joblib")

# Global singleton model container
_MODEL_PACKAGE = None

def get_model():
    global _MODEL_PACKAGE
    if _MODEL_PACKAGE is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run train_model.py first.")
        _MODEL_PACKAGE = joblib.load(MODEL_PATH)
    return _MODEL_PACKAGE

def predict_hotspot_risk(
    rainfall_mm_hr: float,
    cumulative_3h_rain_mm: float,
    elevation_m: float,
    catchment_area_sqkm: float,
    drain_silt_pct: float,
    pump_deployed: int = 0,
    critical_infra_proximity: int = 1
) -> dict:
    """
    Executes real-time inference on a single hotspot feature vector.
    Returns probability, expected water depth, 95% confidence interval, and actionable SOP guidance.
    """
    pkg = get_model()
    clf = pkg["classifier"]
    reg = pkg["regressor"]
    ci_half_width = pkg.get("ci_half_width", 18.0)

    # Prepare vector: 2D numpy array [1, 7]
    X_vec = np.array([[
        float(rainfall_mm_hr),
        float(cumulative_3h_rain_mm),
        float(elevation_m),
        float(catchment_area_sqkm),
        float(drain_silt_pct),
        int(pump_deployed),
        int(critical_infra_proximity)
    ]])

    # 1. Classification & Probability
    probabilities = clf.predict_proba(X_vec)[0] # [p_low, p_watch, p_crit]
    predicted_class = int(np.argmax(probabilities))
    class_label = pkg["class_labels"].get(predicted_class, "LOW_RISK")

    # Overall flood probability: P(watch) + P(critical)
    flood_prob = float(probabilities[1] + probabilities[2]) if len(probabilities) == 3 else float(probabilities[-1])
    flood_prob_pct = round(flood_prob * 100, 1)

    # 2. Regression: Continuous depth in cm
    pred_depth = float(reg.predict(X_vec)[0])
    pred_depth_cm = round(max(0.0, pred_depth), 1)

    ci_low = round(max(0.0, pred_depth_cm - ci_half_width), 1)
    ci_high = round(pred_depth_cm + ci_half_width, 1)

    # 3. Dynamic Lead-Time Action Recommendation
    if pred_depth_cm >= 55.0 or predicted_class == 2:
        action_code = "T-2H RED ALERT"
        action_text = "Deploy high-capacity mobile suction tanker immediately. Lower boom barriers at underpass."
        status_color = "red"
    elif pred_depth_cm >= 25.0 or predicted_class == 1:
        action_code = "T-6H PRE-POSITION"
        action_text = "Stage standby de-watering pump crew on dry high ground. Divert civilian sedans to elevated roads."
        status_color = "amber"
    else:
        action_code = "T-24H CLEAR"
        action_text = "Passable for all civilian vehicles. Normal drainage flow."
        status_color = "emerald"

    return {
        "risk_tier": class_label,
        "flood_probability_pct": flood_prob_pct,
        "predicted_depth_cm": pred_depth_cm,
        "confidence_interval_95": {
            "low_cm": ci_low,
            "high_cm": ci_high,
            "margin_cm": round(ci_half_width, 1)
        },
        "lead_time_action": {
            "window": action_code,
            "recommendation": action_text,
            "color": status_color
        },
        "inputs": {
            "rainfall_mm_hr": rainfall_mm_hr,
            "cumulative_3h_rain_mm": cumulative_3h_rain_mm,
            "drain_silt_pct": drain_silt_pct,
            "pump_deployed": bool(pump_deployed)
        }
    }

def predict_hotspots_batch(
    hotspots: list,
    rainfall_mm_hr: float,
    cumulative_3h_rain_mm: Optional[float] = None,
    pump_active_spot_ids: Optional[set] = None
) -> list:
    """
    Ultra-low latency vectorized batch inference across all 159 Gurugram hotspots.
    Executes in <3ms using Scikit-Learn vector operations.
    """
    if not hotspots:
        return []

    pkg = get_model()
    clf = pkg["classifier"]
    reg = pkg["regressor"]
    ci_half_width = pkg.get("ci_half_width", 18.0)
    pump_set = pump_active_spot_ids or set()

    if cumulative_3h_rain_mm is None:
        cumulative_3h_rain_mm = rainfall_mm_hr * 1.8

    n = len(hotspots)
    X_matrix = np.empty((n, 7), dtype=np.float64)

    for i, h in enumerate(hotspots):
        is_pumped = 1 if (h.get("id") in pump_set or h.get("code") in pump_set or h.get("pump_assigned", False)) else 0
        is_cleaned = h.get("drain_cleaned", False)
        silt = h.get("default_silt_pct", 40.0) * (0.35 if is_cleaned else 1.0)

        X_matrix[i, 0] = rainfall_mm_hr
        X_matrix[i, 1] = cumulative_3h_rain_mm
        X_matrix[i, 2] = h.get("elevation_m", 220.0)
        X_matrix[i, 3] = h.get("catchment_area_sqkm", 5.0)
        X_matrix[i, 4] = silt
        X_matrix[i, 5] = is_pumped
        X_matrix[i, 6] = 1 if h.get("tier") == 1 or "Highway" in h.get("critical_infra", "") else 0

    # Vectorized inference
    probs = clf.predict_proba(X_matrix)
    depths = reg.predict(X_matrix)

    results = []
    for i, h in enumerate(hotspots):
        prob_row = probs[i]
        pred_class = int(np.argmax(prob_row))
        class_label = pkg["class_labels"].get(pred_class, "LOW_RISK")
        flood_prob = float(prob_row[1] + prob_row[2]) if len(prob_row) == 3 else float(prob_row[-1])
        flood_prob_pct = round(flood_prob * 100, 1)

        pred_depth_cm = round(max(0.0, float(depths[i])), 1)
        ci_low = round(max(0.0, pred_depth_cm - ci_half_width), 1)
        ci_high = round(pred_depth_cm + ci_half_width, 1)

        if pred_depth_cm >= 55.0 or pred_class == 2:
            action_window = "T-2H RED ALERT"
            action_text = "Deploy high-capacity mobile suction tanker immediately. Lower boom barriers."
            status_color = "red"
        elif pred_depth_cm >= 25.0 or pred_class == 1:
            action_window = "T-6H PRE-POSITION"
            action_text = "Pre-position mobile pump on dry high ground. Alert RWA / traffic control."
            status_color = "amber"
        else:
            action_window = "T-24H CLEAR"
            action_text = "Passable for all civilian vehicles. Normal drainage flow."
            status_color = "emerald"

        is_pumped = bool(X_matrix[i, 5] == 1)

        results.append({
            "spot_id": h.get("id"),
            "code": h.get("code"),
            "name": h.get("name"),
            "tier": h.get("tier"),
            "tier_label": h.get("tier_label"),
            "sensor_type": h.get("sensor_type"),
            "leg": h.get("leg"),
            "leg_id": h.get("leg_id"),
            "lat": h.get("lat"),
            "lng": h.get("lng"),
            "elevation_m": h.get("elevation_m"),
            "catchment_area_sqkm": h.get("catchment_area_sqkm"),
            "default_silt_pct": h.get("default_silt_pct"),
            "discharge_capacity_cusecs": h.get("discharge_capacity_cusecs"),
            "critical_infra": h.get("critical_infra"),
            "ward": h.get("ward"),
            "recommended_pump_hp": h.get("recommended_pump_hp"),
            "pareto_rank": h.get("pareto_rank"),
            "is_pareto_choke_point": h.get("is_pareto_choke_point", False),
            "pareto_badge": h.get("pareto_badge"),
            "bypass_route": h.get("bypass_route"),
            "pump_deployed": is_pumped,
            "prediction": {
                "risk_tier": class_label,
                "flood_probability_pct": flood_prob_pct,
                "predicted_depth_cm": pred_depth_cm,
                "confidence_interval_95": {
                    "low_cm": ci_low,
                    "high_cm": ci_high,
                    "margin_cm": round(ci_half_width, 1)
                },
                "lead_time_action": {
                    "window": action_window,
                    "recommendation": action_text,
                    "color": status_color
                }
            }
        })

    return results

if __name__ == "__main__":
    # Test sample: Rajiv Chowk Underpass during heavy rain
    result = predict_hotspot_risk(
        rainfall_mm_hr=65.0,
        cumulative_3h_rain_mm=95.0,
        elevation_m=218.0,
        catchment_area_sqkm=14.5,
        drain_silt_pct=48.0,
        pump_deployed=0,
        critical_infra_proximity=1
    )
    print("Test Inference (Rajiv Chowk Underpass - 65 mm/hr Rain):")
    print(json.dumps(result, indent=2))
