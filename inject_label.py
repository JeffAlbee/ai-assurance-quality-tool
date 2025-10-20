import requests
import json

label = {
    "txid": "demo-001",
    "prediction": "safe",
    "model_version": "BridgeTypeModel-v1",
    "violations": ["span_length_m"],
    "metrics": {
        "accuracy": 0.92,
        "f1_score": 0.88,
        "rmse": 1.2,
        "feature_drift": 0.03,
        "domain_violation_count": 2,
        "p95_latency": 180,
        "failure_rate": 0.01,
        "watts_per_inference": 0.5,
        "confidence_floor": 0.81,
        "confidence_variance": 0.04,
        "model_reliability_score": 0.91,
        "audit_governance_score": 0.87,
        "trust_quality_score": 0.89
    },
    "baselines": {
        "accuracy": 0.90,
        "f1_score": 0.85,
        "rmse": 1.5,
        "feature_drift": 0.05,
        "domain_violation_count": 3,
        "p95_latency": 200,
        "failure_rate": 0.02,
        "watts_per_inference": 0.6,
        "confidence_floor": 0.80,
        "confidence_variance": 0.05
    }
}

res = requests.post("http://localhost:8000/v1/labels", json=label)
print(res.status_code, res.json())
