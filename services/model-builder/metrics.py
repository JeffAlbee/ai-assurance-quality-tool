import numpy as np

def compute_metrics(model, recent_data):
    features = recent_data["features"]
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

# Stub functions for now
def calculate_feature_drift(features):
    return 0.02  # placeholder

def check_domain_violations(predictions):
    return 0  # placeholder
