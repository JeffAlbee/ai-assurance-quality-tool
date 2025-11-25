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

# ─────────────────────────────────────────────────────────────
# ✅ SQLAlchemy Imports from orchestration
# ─────────────────────────────────────────────────────────────
from orchestration.db import get_db, Metric
from sqlalchemy import text

# ─────────────────────────────────────────────────────────────
# ✅ Config & Logging
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# ✅ Redis Client
# ─────────────────────────────────────────────────────────────
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# ─────────────────────────────────────────────────────────────
# ✅ Load Ground Truth
# ─────────────────────────────────────────────────────────────
df = pd.read_csv(TRAINING_DATA_PATH)
X = df[["rainfall_mm", "bridge_type_encoded"]].values.tolist()

# Normalize ground truth labels to match prediction vocabulary
y_true_raw = df["target"].tolist()
y_true = []
for label in y_true_raw:
    label = str(label).strip().lower()
    if label in ["low", "flood_risk_low"]:
        y_true.append("flood_risk_low")
    elif label in ["medium", "flood_risk_medium"]:
        y_true.append("flood_risk_medium")
    elif label in ["high", "flood_risk_high"]:
        y_true.append("flood_risk_high")
    else:
        y_true.append(label)  # fallback for unexpected values

input_label_pairs = list(zip(X, y_true))

# ─────────────────────────────────────────────────────────────
# ✅ Poll Model with Traceability Headers
# ─────────────────────────────────────────────────────────────
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
        predictions = result["prediction"]
        latency_ms = result["metrics"].get("p95_latency", 0)
        return predictions, latency_ms
    except Exception as e:
        logging.error(f"[Sidecar] Model polling failed: {e}")
        return None, None

# ─────────────────────────────────────────────────────────────
# ✅ Compute Accuracy & Calibration Metrics
# ─────────────────────────────────────────────────────────────
def compute_accuracy_metrics(y_true, y_pred_raw):
    y_pred = [p["label"] for p in y_pred_raw]
    confidences = [p["confidence"] for p in y_pred_raw]

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")
    confidence_variance = np.var(confidences)

    return {
        "accuracy": float(round(accuracy, 4)),
        "f1_score": float(round(f1, 4)),
        "confidence_variance": float(round(confidence_variance, 4))
    }

# ─────────────────────────────────────────────────────────────
# ✅ Log Metrics to PostgreSQL
# ─────────────────────────────────────────────────────────────
def log_metrics_to_db(metrics):
    db = next(get_db())
    timestamp = datetime.utcnow()
    entries = [
        Metric(model_id=MODEL_ID, metric="accuracy", value=metrics["accuracy"], timestamp=timestamp),
        Metric(model_id=MODEL_ID, metric="f1_score", value=metrics["f1_score"], timestamp=timestamp),
        Metric(model_id=MODEL_ID, metric="confidence_variance", value=metrics["confidence_variance"], timestamp=timestamp)
    ]
    db.add_all(entries)
    db.commit()

# ─────────────────────────────────────────────────────────────
# ✅ Log Predictions to PostgreSQL
# ─────────────────────────────────────────────────────────────
def log_predictions_to_db(inputs, predictions, ground_truths):
    db = next(get_db())
    timestamp = datetime.utcnow()

    for input_data, pred, truth in zip(inputs, predictions, ground_truths):
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
            "predicted_label": pred["label"],
            "confidence_score": pred["confidence"],
            "ground_truth": truth,
            "source": "synthetic",
            "timestamp": timestamp
        })

    db.commit()

# ─────────────────────────────────────────────────────────────
# ✅ Store Metrics in Redis
# ─────────────────────────────────────────────────────────────
def store_metrics_in_redis(metrics):
    try:
        redis_client.set(f"metrics:{MODEL_ID}", json.dumps(metrics))
        logging.info(f"[Sidecar] ✅ Metrics stored in Redis for {MODEL_ID}")
    except Exception as e:
        logging.error(f"[Sidecar] ❌ Failed to store metrics in Redis: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Build Telemetry Payload with TIM Hash (aligned with TIB schema)
# ─────────────────────────────────────────────────────────────
def build_payload(txid, metrics, latency_ms, inputs, predictions, ground_truths):
    payload = {
        "model_id": MODEL_ID,
        "inference_timestamp": int(time.time() * 1000),

        # What was sent to the model
        "request_payload": {"inputs": inputs},

        # What the model returned + metrics
        "response_payload": {
            "predictions": predictions,
            "latency_ms": latency_ms,
            "accuracy": metrics["accuracy"],
            "f1_score": metrics["f1_score"],
            "confidence_variance": metrics["confidence_variance"]
        },

        # Ground truth labels
        "ground_truth": {"labels": ground_truths},

        "system_power_w": SYSTEM_POWER_W,

        # Confidence score: average confidence across predictions
        "confidence_score": float(np.mean([p["confidence"] for p in predictions])) if predictions else 0.0,

        # Attribution vector: placeholder until you have feature attribution logic
        "attribution_vector": [],

        # Features: include the first input vector or flatten as needed
        "features": inputs[0] if inputs else [],

        # Hash for traceability
        "txid_hash": hashlib.sha256(txid.encode()).hexdigest()
    }

    return payload

# ─────────────────────────────────────────────────────────────
# ✅ Send to TIB
# ─────────────────────────────────────────────────────────────
def send_to_tib(payload):
    try:
        response = requests.post(TIB_URL, json=payload)
        logging.info(f"[Sidecar] Telemetry sent to TIB: {payload['txid_hash']} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to send telemetry to TIB: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Send to Assurance Service
# ─────────────────────────────────────────────────────────────
def send_to_assurance(txid, label):
    try:
        response = requests.post(ASSURANCE_URL, json={
            "txid": txid,
            "model_id": MODEL_ID,
            "prediction": label,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        logging.info(f"[Sidecar] Label sent to assurance-service: {txid} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to send label to assurance-service: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Main Loop
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    while True:
        txid = str(uuid.uuid4())
        inputs = [pair[0] for pair in input_label_pairs]
        ground_truths = [pair[1] for pair in input_label_pairs]

        predictions, latency_ms = poll_model(inputs, txid)

        if predictions:
            metrics = compute_accuracy_metrics(ground_truths, predictions)
            log_metrics_to_db(metrics)
            store_metrics_in_redis(metrics)
            log_predictions_to_db(inputs, predictions, ground_truths)
            payload = build_payload(txid, metrics, latency_ms, inputs, predictions, ground_truths)
            send_to_tib(payload)
            send_to_assurance(txid, predictions[0]["label"])

            logging.info(
                f"[Sidecar] ✅ Accuracy: {metrics['accuracy']} | "
                f"F1: {metrics['f1_score']} | "
                f"Confidence Var: {metrics['confidence_variance']}"
            )   
            time.sleep(POLL_INTERVAL)
