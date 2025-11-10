import numpy as np
from typing import List, Dict, Any

def compute_metrics(model, recent_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute evaluation metrics for a given model and recent input data.

    Args:
        model: A model object with a .predict(features) method.
        recent_data: A dictionary containing:
            - "features": List of input feature vectors
            - "labels": Ground truth labels (0 or 1)
            - Optional: latency, failures, watts, confidence_floor, confidence_variance

    Returns:
        A dictionary of computed metrics.
    """
    features: List[List[float]] = recent_data["features"]
    labels = np.array(recent_data["labels"])

    # Run predictions
    predictions = model.predict(features)

    # Convert predicted labels to binary: unsafe → 1, safe → 0
    predicted_labels = np.array([
        1 if p["label"] == "unsafe" else 0
        for p in predictions
    ])

    # Accuracy and RMSE
    accuracy = np.mean(predicted_labels == labels)
    rmse = np.sqrt(np.mean((predicted_labels - labels) ** 2))

    # Optional: stub drift and violation checks
    drift_score = calculate_feature_drift(features)
    violations = check_domain_violations(predictions)

    return {
        "accuracy": round(float(accuracy), 3),
        "rmse": round(float(rmse), 2),
        "feature_drift": drift_score,
        "domain_violation_count": violations,
        "p95_latency": recent_data.get("latency", 180),
        "failure_rate": recent_data.get("failures", 0.01),
        "watts_per_inference": recent_data.get("watts", 0.5),
        "confidence_floor": recent_data.get("confidence_floor", 0.81),
        "confidence_variance": recent_data.get("confidence_variance", 0.04)
    }

# ─────────────────────────────────────────────────────────────
# 🔧 Stub Functions (to be replaced with real logic)
# ─────────────────────────────────────────────────────────────

def calculate_feature_drift(features: List[List[float]]) -> float:
    """Placeholder for feature drift detection."""
    return 0.02

def check_domain_violations(predictions: List[Dict[str, Any]]) -> int:
    """Placeholder for domain-specific rule violations."""
    return 0
