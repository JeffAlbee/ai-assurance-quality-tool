import numpy as np
import logging
from typing import List, Dict, Any
from sklearn.metrics import f1_score

# ─────────────────────────────────────────────────────────────
# ✅ Logging setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("metrics")

def _to_float_list(row: Any) -> List[float]:
    """Safely cast a row of feature values to floats."""
    try:
        return [float(x) for x in row]
    except Exception as e:
        logger.error(f"[METRICS] ❌ Failed to cast feature row to floats: row={row} error={e}")
        raise

def _to_str_labels(labels_in: Any) -> np.ndarray:
    """Cast labels to lowercase string array for categorical comparison."""
    try:
        cleaned = [str(l).strip().lower() for l in labels_in]
        return np.array(cleaned, dtype=object)
    except Exception as e:
        logger.error(f"[METRICS] ❌ Failed to cast labels: labels_in={labels_in} error={e}")
        raise

def _to_str_prediction(pred_label: Any) -> str:
    """Normalize prediction labels to lowercase strings."""
    try:
        return str(pred_label).strip().lower()
    except Exception as e:
        logger.error(f"[METRICS] ❌ Failed to cast prediction label: pred_label={pred_label} error={e}")
        raise

def _to_float(value: Any, default: float) -> float:
    """Cast to float with a fallback default if value is falsy or invalid."""
    try:
        v = value if value not in (None, "") else default
        return float(v)
    except Exception:
        return float(default)

def compute_metrics(predictions: List[Dict[str, Any]], recent_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute evaluation metrics for a given set of predictions and recent input data.
    Predictions are passed in directly from app.py (already categorical).
    """
    try:
        # 🔎 Log the entire payload immediately
        logger.info(f"[METRICS] FULL recent_data payload={recent_data}")
        logger.info(f"[METRICS] Incoming recent_data keys={list(recent_data.keys())}")

        # Features
        raw_features = recent_data.get("features", [])
        logger.info(f"[METRICS] Raw features={raw_features}")
        features: List[List[float]] = [_to_float_list(row) for row in raw_features]

        # Labels
        raw_labels = recent_data.get("labels", [])
        logger.info(f"[METRICS] Raw labels={raw_labels}")
        labels = _to_str_labels(raw_labels)
        logger.info(f"[METRICS] Labels cast={labels}")

        if len(features) == 0 or labels.size == 0:
            raise ValueError("Missing or empty features/labels")

        # Predictions (already categorical, passed in from app.py)
        logger.info(f"[METRICS] Predictions raw={predictions}")
        predicted_labels = np.array(
            [_to_str_prediction(p.get("label")) for p in predictions],
            dtype=object
        )
        logger.info(f"[METRICS] Predictions cast={predicted_labels}")

        if predicted_labels.size != labels.size:
            raise ValueError(f"Predictions/labels length mismatch: preds={predicted_labels.size}, labels={labels.size}")

        # Accuracy
        accuracy = float(np.mean(predicted_labels == labels))

        # F1 score (macro average across categories)
        f1 = f1_score(labels, predicted_labels, average="macro")

        # RMSE (map categories to integers for distance calculation)
        category_map = {"flood_risk_low": 0, "flood_risk_medium": 1, "flood_risk_high": 2}
        label_ints = np.array([category_map.get(l, 0) for l in labels])
        pred_ints = np.array([category_map.get(p, 0) for p in predicted_labels])
        rmse = float(np.sqrt(np.mean((pred_ints - label_ints) ** 2)))

        # Stub drift/violations
        drift_score = float(calculate_feature_drift(features))
        violations = int(check_domain_violations(predictions))

        # Optional values
        p95_latency = _to_float(recent_data.get("latency", 180), 180.0)
        failure_rate = _to_float(recent_data.get("failures", 0.01), 0.01)
        watts = _to_float(recent_data.get("watts", 0.5), 0.5)
        confidence_floor = _to_float(recent_data.get("confidence_floor", 0.81), 0.81)
        confidence_variance = _to_float(recent_data.get("confidence_variance", 0.04), 0.04)

        logger.info(
            f"[METRICS] Computed "
            f"accuracy={accuracy}, f1={f1}, rmse={rmse}, drift={drift_score}, violations={violations} | "
            f"latency={p95_latency}, failures={failure_rate}, watts={watts}, floor={confidence_floor}, var={confidence_variance}"
        )

        return {
            "accuracy": round(accuracy, 3),
            "f1_score": round(f1, 3),
            "rmse": round(rmse, 2),
            "feature_drift": drift_score,
            "domain_violation_count": violations,
            "p95_latency": p95_latency,
            "failure_rate": failure_rate,
            "watts_per_inference": watts,
            "confidence_floor": confidence_floor,
            "confidence_variance": confidence_variance
        }

    except Exception as e:
        logger.error(f"[METRICS] ❌ Metric computation failed: {e}")
        return {
            "accuracy": 0.0,
            "f1_score": 0.0,
            "rmse": 0.0,
            "feature_drift": 0.0,
            "domain_violation_count": 0,
            "p95_latency": 180.0,
            "failure_rate": 0.01,
            "watts_per_inference": 0.5,
            "confidence_floor": 0.81,
            "confidence_variance": 0.04
        }

# ─────────────────────────────────────────────────────────────
# 🔧 Stub functions
# ─────────────────────────────────────────────────────────────
def calculate_feature_drift(features: List[List[float]]) -> float:
    return 0.02

def check_domain_violations(predictions: List[Dict[str, Any]]) -> int:
    return 0
