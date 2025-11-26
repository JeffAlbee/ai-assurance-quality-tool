import time
import uuid
import hashlib
import requests
import json
import logging
import os
import pandas as pd
import numpy as np
import redis
from sklearn.metrics import accuracy_score, f1_score
from datetime import datetime
from collections import Counter

def log_confusion_summary(y_true, predictions):
    # Normalize predictions for consistency
    pred_labels = [normalize_label(p.get("label", "")) for p in predictions]
    gt_labels = [normalize_label(gt) for gt in y_true]

    # Count distributions
    gt_counts = Counter(gt_labels)
    pred_counts = Counter(pred_labels)

    # Build mismatch summary
    mismatches = [(gt, pred) for gt, pred in zip(gt_labels, pred_labels) if gt != pred]
    mismatch_sample = mismatches[:10]  # show first 10 mismatches

    logging.info(f"[Sidecar-Diagnostics] Ground truth distribution: {gt_counts}")
    logging.info(f"[Sidecar-Diagnostics] Prediction distribution: {pred_counts}")
    logging.info(f"[Sidecar-Diagnostics] Total mismatches: {len(mismatches)}")
    if mismatch_sample:
        logging.info(f"[Sidecar-Diagnostics] Sample mismatches (GT vs Pred): {mismatch_sample}")

    # Optional: confusion matrix
    try:
        cm = pd.crosstab(pd.Series(gt_labels, name="GT"), pd.Series(pred_labels, name="Pred"))
        logging.info(f"[Sidecar-Diagnostics] Confusion matrix:\n{cm}")
    except Exception as e:
        logging.warning(f"[Sidecar-Diagnostics] Could not compute confusion matrix: {e}")

# ✅ SQLAlchemy Imports from orchestration
from orchestration.db import get_db, Metric
from sqlalchemy import text

# ✅ Config & Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MODEL_URL = os.getenv("MODEL_URL", "http://model-builder:9000/predict")
TIB_URL = os.getenv("TIB_URL", "http://tib-producer-api:8002/ingest")
ASSURANCE_URL = os.getenv("ASSURANCE_URL", "http://assurance-service:8000/v1/labels")
MODEL_ID = os.getenv("MODEL_ID", "flood-risk-predictor")
SYSTEM_POWER_W = float(os.getenv("SYSTEM_POWER_W", "42.0"))
TRAINING_DATA_PATH = os.getenv("TRAINING_DATA_PATH", "/app/training_data.csv")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# ✅ Redis Client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ✅ Label normalization helpers
NORMALIZATION_MAP = {
    "low": "flood_risk_low",
    "flood_risk_low": "flood_risk_low",
    "medium": "flood_risk_medium",
    "flood_risk_medium": "flood_risk_medium",
    "high": "flood_risk_high",
    "flood_risk_high": "flood_risk_high",
}

def normalize_label(label: str) -> str:
    lab = str(label).strip().lower()
    return NORMALIZATION_MAP.get(lab, lab)

def normalize_labels(labels):
    return [normalize_label(l) for l in labels]

# ✅ Load Ground Truth
try:
    df = pd.read_csv(TRAINING_DATA_PATH)
    X = df[["rainfall_mm", "bridge_type_encoded"]].values.tolist()

    y_true_raw = df["target"].tolist()
    y_true = normalize_labels(y_true_raw)

    input_label_pairs = list(zip(X, y_true))

    logging.info(f"[Sidecar] Ground truth loaded: {len(y_true)} labels")
    logging.info(f"[Sidecar] Ground truth unique classes: {sorted(set(y_true))}")
except Exception as e:
    logging.error(f"[Sidecar] Failed to load training data: {e}")
    raise

# ✅ Poll Model with Traceability Headers
def poll_model(batch, txid):
    headers = {
        "X-Model-ID": MODEL_ID,
        "X-TXID": txid,
        "X-Sidecar-Agent": "true"
    }
    try:
        response = requests.post(MODEL_URL, json={"inputs": batch}, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        predictions = result.get("prediction", [])
        latency_ms = result.get("metrics", {}).get("p95_latency", 0)

        # Log a small sample of raw predictions for diagnostics
        sample_preds = predictions[:5]
        logging.info(f"[Sidecar] Model polled: preds_sample={sample_preds} latency_ms={latency_ms}")
        return predictions, latency_ms
    except Exception as e:
        logging.error(f"[Sidecar] Model polling failed: {e}")
        return None, None

# ✅ Compute Accuracy & Calibration Metrics
def compute_accuracy_metrics(y_true, y_pred_raw):
    if not y_pred_raw:
        logging.warning("[Sidecar] No predictions returned; metrics will be zero.")
        return {"accuracy": 0.0, "f1_score": 0.0, "confidence_variance": 0.0}

    # Normalize predicted labels to match ground truth vocabulary
    y_pred_labels_raw = [p.get("label", "") for p in y_pred_raw]
    y_pred = normalize_labels(y_pred_labels_raw)

    confidences = [p.get("confidence", 0.0) for p in y_pred_raw]

    # Diagnostics: class coverage and mismatches
    gt_classes = set(y_true)
    pred_classes = set(y_pred)
    logging.info(f"[Sidecar] GT classes: {sorted(gt_classes)} | Pred classes: {sorted(pred_classes)}")

    # If predictions miss classes present in GT, F1 may be low/zero; log it explicitly
    missing_in_pred = gt_classes - pred_classes
    if missing_in_pred:
        logging.warning(f"[Sidecar] Predicted labels missing GT classes: {sorted(missing_in_pred)}")

    # Log small samples for alignment inspection
    logging.info(f"[Sidecar] Sample y_true: {y_true[:5]}")
    logging.info(f"[Sidecar] Sample y_pred: {y_pred[:5]}")

    # Compute metrics
    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")
    confidence_variance = float(np.var(confidences))

    metrics = {
        "accuracy": float(round(accuracy, 4)),
        "f1_score": float(round(f1, 4)),
        "confidence_variance": float(round(confidence_variance, 4)),
    }
    logging.info(f"[Sidecar] Computed metrics: {metrics}")
    return metrics

# ✅ Log Metrics to PostgreSQL
def log_metrics_to_db(metrics):
    try:
        db = next(get_db())
        timestamp = datetime.utcnow()
        entries = [
            Metric(model_id=MODEL_ID, metric="accuracy", value=metrics["accuracy"], timestamp=timestamp),
            Metric(model_id=MODEL_ID, metric="f1_score", value=metrics["f1_score"], timestamp=timestamp),
            Metric(model_id=MODEL_ID, metric="confidence_variance", value=metrics["confidence_variance"], timestamp=timestamp),
        ]
        db.add_all(entries)
        db.commit()
        logging.info(f"[Sidecar] Metrics persisted to DB at {timestamp.isoformat()}Z")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to persist metrics to DB: {e}")

# ✅ Log Predictions to PostgreSQL
def log_predictions_to_db(inputs, predictions, ground_truths):
    try:
        db = next(get_db())
        timestamp = datetime.utcnow()
        for input_data, pred, truth in zip(inputs, predictions, ground_truths):
            # Normalize predicted label before persisting for consistency
            normalized_label = normalize_label(pred.get("label", ""))
            confidence = float(pred.get("confidence", 0.0))

            db.execute(text("""
                INSERT INTO predictions (
                    model_id, input_data, predicted_label, confidence_score, ground_truth, source, timestamp
                ) VALUES (
                    :model_id, :input_data, :predicted_label, :confidence_score, :ground_truth, :source, :timestamp
                )
            """), {
                "model_id": MODEL_ID,
                "input_data": json.dumps({
                    "rainfall_mm": input_data[0],
                    "bridge_type_encoded": input_data[1]
                }),
                "predicted_label": normalized_label,
                "confidence_score": confidence,
                "ground_truth": truth,
                "source": "synthetic",
                "timestamp": timestamp
            })

        db.commit()
        logging.info(f"[Sidecar] {len(ground_truths)} predictions persisted to DB at {timestamp.isoformat()}Z")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to persist predictions to DB: {e}")

# ✅ Store Metrics in Redis
def store_metrics_in_redis(metrics):
    try:
        redis_client.set(f"metrics:{MODEL_ID}", json.dumps(metrics))
        logging.info(f"[Sidecar] Metrics stored in Redis for {MODEL_ID}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to store metrics in Redis: {e}")

# ✅ Build Telemetry Payload with TIM Hash (aligned with TIB schema)
def build_payload(txid, metrics, latency_ms, inputs, predictions, ground_truths):
    # Normalize predictions in payload for consistency
    normalized_predictions = []
    for p in predictions or []:
        normalized_predictions.append({
            "label": normalize_label(p.get("label", "")),
            "confidence": float(p.get("confidence", 0.0))
        })

    payload = {
        "model_id": MODEL_ID,
        "inference_timestamp": int(time.time() * 1000),
        "request_payload": {"inputs": inputs},
        "response_payload": {
            "predictions": normalized_predictions,
            "latency_ms": latency_ms,
            "accuracy": metrics["accuracy"],
            "f1_score": metrics["f1_score"],
            "confidence_variance": metrics["confidence_variance"],
        },
        "ground_truth": {"labels": ground_truths},
        "system_power_w": SYSTEM_POWER_W,
        "confidence_score": float(np.mean([p["confidence"] for p in normalized_predictions])) if normalized_predictions else 0.0,
        "attribution_vector": [],
        "features": inputs[0] if inputs else [],
        "txid_hash": hashlib.sha256(txid.encode()).hexdigest(),
    }
    return payload

# ✅ Send to TIB
def send_to_tib(payload):
    try:
        response = requests.post(TIB_URL, json=payload, timeout=10)
        logging.info(f"[Sidecar] Telemetry sent to TIB: {payload['txid_hash']} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to send telemetry to TIB: {e}")

# ✅ Send to Assurance Service
def send_to_assurance(txid, label):
    try:
        response = requests.post(ASSURANCE_URL, json={
            "txid": txid,
            "model_id": MODEL_ID,
            "prediction": label,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }, timeout=10)
        logging.info(f"[Sidecar] Label sent to assurance-service: {txid} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to send label to assurance-service: {e}")

# ✅ Main Loop
if __name__ == "__main__":
    while True:
        txid = str(uuid.uuid4())
        inputs = [pair[0] for pair in input_label_pairs]
        ground_truths = [pair[1] for pair in input_label_pairs]

        predictions, latency_ms = poll_model(inputs, txid)

        if predictions:
            # Compute metrics with normalized predictions and diagnostic logging
            metrics = compute_accuracy_metrics(ground_truths, predictions)

            log_confusion_summary(ground_truths, predictions) 

            # Persist and publish
            log_metrics_to_db(metrics)
            store_metrics_in_redis(metrics)
            log_predictions_to_db(inputs, predictions, ground_truths)

            payload = build_payload(txid, metrics, latency_ms, inputs, predictions, ground_truths)
            send_to_tib(payload)

            # Send first prediction's normalized label to assurance service
            first_label = normalize_label(predictions[0].get("label", ""))
            send_to_assurance(txid, first_label)

            

            logging.info(
                f"[Sidecar] Loop complete | Accuracy={metrics['accuracy']} | "
                f"F1={metrics['f1_score']} | ConfVar={metrics['confidence_variance']} | "
                f"Latency(ms)={latency_ms} | TXID={txid}"
            )
        else:
            logging.warning("[Sidecar] No predictions returned; skipping metrics/persistence this cycle.")

        time.sleep(POLL_INTERVAL)
