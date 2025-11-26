import numpy as np
import logging
from typing import List, Dict, Any
from sklearn.metrics import f1_score

# ─────────────────────────────────────────────────────────────
# ✅ Logging setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("metrics")

# ─────────────────────────────────────────────────────────────
# ✅ Shared normalization (aligned with sidecar-agent)
# ─────────────────────────────────────────────────────────────
NORMALIZATION_MAP = {
    "low": "flood_risk_low",
    "flood_risk_low": "flood_risk_low",
    "medium": "flood_risk_medium",
    "flood_risk_medium": "flood_risk_medium",
    "high": "flood_risk_high",
    "flood_risk_high": "flood_risk_high",
}

def normalize_label(label: Any) -> str:
    lab = str(label).strip().lower()
    return NORMALIZATION_MAP.get(lab, lab)

def normalize_labels(labels_in: List[Any]) -> np.ndarray:
    return np.array([normalize_label(l) for l in labels_in], dtype=object)

# ─────────────────────────────────────────────────────────────
# ✅ Casting helpers
# ─────────────────────────────────────────────────────────────
def _to_float_list(row: Any) -> List[float]:
    """Safely cast a row of feature values to floats."""
    try:
        return [float(x) for x in row]
    except Exception as e:
        logger.error(f"[METRICS] ❌ Failed to cast feature row to floats: row={row} error={e}")
        raise

def _to_float(value: Any, default: float) -> float:
    """Cast to float with a fallback default if value is falsy or invalid."""
    try:
        v = value if value not in (None, "") else default
        return float(v)
    except Exception:
        return float(default)

# ─────────────────────────────────────────────────────────────
# ✅ Core computation
# ─────────────────────────────────────────────────────────────
def compute_metrics(predictions: List[Dict[str, Any]], recent_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute evaluation metrics given predictions and recent input data.
    - Normalizes labels for categorical consistency
    - Logs class coverage and mismatches
    """
    try:
        # 🔎 Log the payload (trimmed to key fields to avoid noise)
        logger.info(f"[METRICS] Incoming keys={list(recent_data.keys())}")
        raw_features = recent_data.get("features", [])
        raw_labels = recent_data.get("labels", [])
        logger.info(f"[METRICS] Features count={len(raw_features)} | Labels count={len(raw_labels)}")
        logger.info(f"[METRICS] Labels sample={raw_labels[:5]}")
        logger.info(f"[METRICS] Predictions sample={predictions[:5]}")

        # Cast features
        features: List[List[float]] = [_to_float_list(row) for row in raw_features]

        # Normalize ground truth labels
        labels = normalize_labels(raw_labels)

        if len(features) == 0 or labels.size == 0:
            raise ValueError("Missing or empty features/labels")

        # Normalize predicted labels
        predicted_labels = normalize_labels([p.get("label", "") for p in predictions])

        # Confidence variance from recent_data or fallback to variance of provided confidences
        if "confidence_variance" in recent_data:
            confidence_variance = _to_float(recent_data.get("confidence_variance"), 0.04)
        else:
            confs = [float(p.get("confidence", 0.0)) for p in predictions] if predictions else []
            confidence_variance = float(np.var(confs)) if confs else 0.0

        # Defensive checks
        if predicted_labels.size == 0:
            logger.warning("[METRICS] No predicted labels; metrics will be zero.")
            return _fallback_metrics(recent_data, confidence_variance)

        if predicted_labels.size != labels.size:
            logger.warning(
                f"[METRICS] Length mismatch: preds={predicted_labels.size} vs labels={labels.size} "
                f"→ Truncating to min length to compute metrics."
            )
            n = min(predicted_labels.size, labels.size)
            predicted_labels = predicted_labels[:n]
            labels = labels[:n]
            features = features[:n]

        # Class coverage diagnostics
        gt_classes = set(labels.tolist())
        pred_classes = set(predicted_labels.tolist())
        missing_in_pred = gt_classes - pred_classes
        logger.info(f"[METRICS] GT classes={sorted(gt_classes)} | Pred classes={sorted(pred_classes)}")
        if missing_in_pred:
            logger.warning(f"[METRICS] Predicted labels missing GT classes: {sorted(missing_in_pred)}")

        # Accuracy
        accuracy = float(np.mean(predicted_labels == labels))

        # F1 score (weighted is more stable with class imbalance)
        f1 = f1_score(labels, predicted_labels, average="weighted")

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

        logger.info(
            f"[METRICS] Computed accuracy={accuracy:.4f}, f1={f1:.4f}, rmse={rmse:.2f}, "
            f"drift={drift_score}, violations={violations} | "
            f"latency={p95_latency}, failures={failure_rate}, watts={watts}, "
            f"floor={confidence_floor}, var={confidence_variance}"
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
            "confidence_variance": confidence_variance,
        }

    except Exception as e:
        logger.error(f"[METRICS] ❌ Metric computation failed: {e}")
        return _fallback_metrics(recent_data, recent_data.get("confidence_variance", 0.04))

# ─────────────────────────────────────────────────────────────
# 🔧 Fallback and stubs
# ─────────────────────────────────────────────────────────────
def _fallback_metrics(recent_data: Dict[str, Any], confidence_variance_fallback: float) -> Dict[str, float]:
    p95_latency = _to_float(recent_data.get("latency", 180), 180.0)
    failure_rate = _to_float(recent_data.get("failures", 0.01), 0.01)
    watts = _to_float(recent_data.get("watts", 0.5), 0.5)
    confidence_floor = _to_float(recent_data.get("confidence_floor", 0.81), 0.81)
    confidence_variance = _to_float(confidence_variance_fallback, 0.04)
    return {
        "accuracy": 0.0,
        "f1_score": 0.0,
        "rmse": 0.0,
        "feature_drift": 0.0,
        "domain_violation_count": 0,
        "p95_latency": p95_latency,
        "failure_rate": failure_rate,
        "watts_per_inference": watts,
        "confidence_floor": confidence_floor,
        "confidence_variance": confidence_variance,
    }

def calculate_feature_drift(features: List[List[float]]) -> float:
    return 0.02

def check_domain_violations(predictions: List[Dict[str, Any]]) -> int:
    return 0
