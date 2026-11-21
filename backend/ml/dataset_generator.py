"""
NeerNetra - JalRakshak NCR
Dataset Generator using pure NumPy & Python csv (Zero-Dependency on pandas)
Calibrated against Gurugram historical monsoon flood data:
- 2016 'Gurujam' (NH-48 standstill)
- July 2023 (80+ hours waterlogging, Badshahpur basin surge)
- July 2025 (133mm in 12hrs)
- Sept 2025 (133mm in 4hrs, 20km jam)
"""

import numpy as np
import csv
import os

np.random.seed(42)

FEATURE_NAMES = [
    "rainfall_mm_hr",
    "cumulative_3h_rain_mm",
    "elevation_m",
    "catchment_area_sqkm",
    "drain_silt_pct",
    "pump_deployed",
    "critical_infra_proximity"
]

ALL_COLUMNS = FEATURE_NAMES + ["water_depth_cm", "is_flooded", "flood_class"]

def generate_gurugram_monsoon_dataset(n_samples=3000):
    # 1. Feature: Rainfall Intensity (mm/hr) (0 to 150 mm/hr)
    rainfall_intensity = np.random.exponential(scale=25, size=n_samples)
    rainfall_intensity = np.clip(rainfall_intensity, 0, 150)

    # 2. Feature: 3-Hour Cumulative Precipitation (mm)
    cumulative_3h_rain = rainfall_intensity * np.random.uniform(1.2, 3.2, size=n_samples)
    cumulative_3h_rain = np.clip(cumulative_3h_rain, 0, 220)

    # 3. Feature: Spot Elevation (meters) (Low-lying Khandsa ~214m to Golf Course ~242m)
    elevation_m = np.random.uniform(212, 245, size=n_samples)

    # 4. Feature: Upstream Catchment Area (sq km)
    catchment_area_sqkm = np.random.uniform(1.5, 38.0, size=n_samples)

    # 5. Feature: Drain Siltation Percentage (0% to 100%) - CAG 2023 baseline ~45%
    drain_silt_pct = np.random.beta(a=2.5, b=2.8, size=n_samples) * 100

    # 6. Feature: Pump Pre-Deployed Status (0 = None, 1 = Active 5000 GPM pump)
    pump_deployed = np.random.choice([0, 1], p=[0.72, 0.28], size=n_samples)

    # 7. Feature: Critical Infrastructure Proximity (1 = Highway/Underpass/Hospital)
    critical_infra_proximity = np.random.choice([0, 1], p=[0.45, 0.55], size=n_samples)

    # Rational Runoff Hydro Dynamics: Q = C * I * A + Depression Pooling
    elevation_penalty = np.maximum(0, (230 - elevation_m) * 2.2)
    silt_multiplier = 1.0 + (drain_silt_pct / 100.0) * 1.6
    rain_factor = (rainfall_intensity * 0.55) + (cumulative_3h_rain * 0.25)

    base_water_depth = (rain_factor * (catchment_area_sqkm / 12.0) * silt_multiplier) + elevation_penalty

    # Mitigation discount: Active high-capacity pump removes ~65% of flood accumulation
    mitigation_discount = np.where(pump_deployed == 1, 0.35, 1.0)
    final_water_depth = base_water_depth * mitigation_discount
    final_water_depth += np.random.normal(0, 3.5, size=n_samples)
    final_water_depth = np.clip(final_water_depth, 0, 180).round(1)

    # 3-Tier Classification:
    # 0 = LOW RISK (< 25 cm)
    # 1 = WATCH (25 - 55 cm)
    # 2 = CRITICAL FLOOD (> 55 cm)
    flood_class = np.zeros(n_samples, dtype=int)
    flood_class[final_water_depth >= 25] = 1
    flood_class[final_water_depth >= 55] = 2
    is_flooded = (final_water_depth >= 25).astype(int)

    # Stack into 2D array
    X = np.column_stack([
        np.round(rainfall_intensity, 1),
        np.round(cumulative_3h_rain, 1),
        np.round(elevation_m, 1),
        np.round(catchment_area_sqkm, 1),
        np.round(drain_silt_pct, 1),
        pump_deployed,
        critical_infra_proximity
    ])

    return X, final_water_depth, is_flooded, flood_class

def save_dataset_csv(filepath, n_samples=3000):
    X, final_water_depth, is_flooded, flood_class = generate_gurugram_monsoon_dataset(n_samples)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ALL_COLUMNS)
        for i in range(len(X)):
            row = list(X[i]) + [final_water_depth[i], is_flooded[i], flood_class[i]]
            writer.writerow(row)
            
    print(f"[+] Saved {n_samples} samples to {filepath}")
    return X, final_water_depth, is_flooded, flood_class

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    out_csv = os.path.join(out_dir, "gurugram_flood_training_data.csv")
    save_dataset_csv(out_csv)
