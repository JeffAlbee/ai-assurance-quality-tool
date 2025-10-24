def compute_metrics():
    return {
        "accuracy": 0.92,
        "rmse": 1.2,
        "feature_drift": 0.03,
        "domain_violation_count": 2,
        "p95_latency": 180,
        "failure_rate": 0.01,
        "watts_per_inference": 0.5,
        "confidence_floor": 0.81,
        "confidence_variance": 0.04
    }
