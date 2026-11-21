"""
NeerNetra - JalRakshak NCR
Explainable Machine Learning Model Training Pipeline (Deliverable 2)
Pure NumPy & Scikit-Learn (Zero-Dependency on pandas)

Models Trained:
1. Explainable Gradient Boosting Classifier: Predicts 3-tier risk (LOW, WATCH, CRITICAL) & probability
2. Explainable Gradient Boosting Regressor: Predicts expected water depth (cm) with 95% Confidence Intervals
"""

import os
import sys
import json
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from dataset_generator import generate_gurugram_monsoon_dataset, FEATURE_NAMES

def train_and_export_models():
    print("=" * 70)
    print("  Team NeerNetra | JalRakshak NCR Explainable ML Pipeline (Deliverable 2)")
    print("=" * 70)

    # 1. Generate calibrated Gurugram storm dataset
    print("[*] Synthesizing calibrated Gurugram storm dataset (3,200 events)...")
    X, y_depth, is_flooded, y_class = generate_gurugram_monsoon_dataset(n_samples=3200)

    # 2. Train/Test Split (80% Train, 20% Holdout Test)
    X_train, X_test, y_class_train, y_class_test, y_depth_train, y_depth_test = train_test_split(
        X, y_class, y_depth, test_size=0.20, random_state=42, stratify=y_class
    )
    print(f"[*] Training samples: {len(X_train)} | Holdout validation samples: {len(X_test)}")

    # 3. Model 1: Explainable Risk Classifier (Traffic-Light & Probability)
    print("\n[*] Training Explainable Risk Classifier (GradientBoostingClassifier)...")
    clf = GradientBoostingClassifier(
        n_estimators=75,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    clf.fit(X_train, y_class_train)

    y_class_pred = clf.predict(X_test)
    class_acc = accuracy_score(y_class_test, y_class_pred)
    print(f"  -> Classifier Accuracy: {class_acc * 100:.2f}%")

    # 4. Model 2: Depth Regressor with Confidence Intervals
    print("[*] Training Water Depth Regressor (GradientBoostingRegressor)...")
    reg = GradientBoostingRegressor(
        n_estimators=85,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    reg.fit(X_train, y_depth_train)

    y_depth_pred = reg.predict(X_test)
    mae = mean_absolute_error(y_depth_test, y_depth_pred)
    r2 = r2_score(y_depth_test, y_depth_pred)
    residual_std = np.std(y_depth_test - y_depth_pred)
    ci_half_width = 1.96 * residual_std

    print(f"  -> Depth Mean Absolute Error (MAE): {mae:.2f} cm")
    print(f"  -> Depth R-Squared (R2 Score): {r2:.4f}")
    print(f"  -> 95% Confidence Interval Half-Width: ±{ci_half_width:.1f} cm")

    # 5. Extract Feature Importances (Essential for Municipal Explainability)
    importances = clf.feature_importances_
    feature_ranking = sorted(
        zip(FEATURE_NAMES, importances),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\n[*] Feature Importance Breakdown (Municipal Transparency):")
    for feat, imp in feature_ranking:
        bar = "█" * int(imp * 30)
        print(f"  - {feat:26s}: {imp * 100:5.1f}% {bar}")

    # 6. Save Model Package & Metadata
    models_dir = os.path.join(curr_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    model_artifact_path = os.path.join(models_dir, "flood_model.joblib")
    meta_path = os.path.join(models_dir, "model_metadata.json")

    package = {
        "classifier": clf,
        "regressor": reg,
        "features": FEATURE_NAMES,
        "class_labels": {0: "LOW_RISK", 1: "WATCH", 2: "CRITICAL"},
        "residual_std": float(residual_std),
        "ci_half_width": float(ci_half_width),
        "mae": float(mae),
        "accuracy": float(class_acc)
    }
    joblib.dump(package, model_artifact_path)
    print(f"\n[+] Saved trained model package to: {model_artifact_path}")

    metadata = {
        "model_version": "1.0.0-NeerNetra",
        "algorithm": "GradientBoostedTrees (Scikit-Learn)",
        "features": FEATURE_NAMES,
        "accuracy_pct": round(float(class_acc) * 100, 2),
        "mae_cm": round(float(mae), 2),
        "r2_score": round(float(r2), 4),
        "ci_half_width_cm": round(float(ci_half_width), 1),
        "feature_importances": {feat: round(float(imp) * 100, 2) for feat, imp in feature_ranking},
        "target_municipality": "Municipal Corporation of Gurugram (MCG)",
        "deliverable": "Deliverable 2 - AI Predictive System Architecture",
        "team": "NeerNetra"
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Saved model explainability metadata to: {meta_path}")
    print("=" * 70)

    return metadata

if __name__ == "__main__":
    train_and_export_models()
