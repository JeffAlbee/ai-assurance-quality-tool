from fastapi import FastAPI, Request
from pydantic import BaseModel
from model import load_model
from metrics import compute_metrics
import time
import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import numpy as np

# ─────────────────────────────────────────────────────────────
# ✅ Environment Setup
# ─────────────────────────────────────────────────────────────
load_dotenv()
MODEL_ID = os.getenv("MODEL_ID", "flood-risk-predictor")

# ─────────────────────────────────────────────────────────────
# ✅ Logging Setup (Rotating File + Console)
# ─────────────────────────────────────────────────────────────
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, "inference.log"),
    maxBytes=5_000_000,
    backupCount=3
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[file_handler, logging.StreamHandler()]
)

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI App Initialization
# ─────────────────────────────────────────────────────────────
app = FastAPI()
model = load_model(MODEL_ID)

# ─────────────────────────────────────────────────────────────
# ✅ Input Schema
# ─────────────────────────────────────────────────────────────
class InputBatch(BaseModel):
    inputs: list[list[float]]  # e.g., [[74.9, 2], [146.4, 2]]

# ─────────────────────────────────────────────────────────────
# ✅ Label Normalization (shared with sidecar-agent)
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# ✅ Helper: Sanitize Metrics for JSON
# ─────────────────────────────────────────────────────────────
def sanitize_metrics(metrics: dict) -> dict:
    return {
        k: (0.0 if isinstance(v, float) and (np.isnan(v) or np.isinf(v)) else v)
        for k, v in metrics.items()
    }

# ─────────────────────────────────────────────────────────────
# ✅ Health Check Endpoint
# ─────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ─────────────────────────────────────────────────────────────
# ✅ Prediction Endpoint with Header Logging
# ─────────────────────────────────────────────────────────────
@app.post("/predict")
async def predict_endpoint(request: Request):
    headers = dict(request.headers)
    txid = headers.get("x-txid", "unknown")
    model_id = headers.get("x-model-id", MODEL_ID)
    agent_flag = headers.get("x-sidecar-agent", "false")

    logging.info(f"[Model] Inference request | TXID={txid} | Model-ID={model_id} | Sidecar-Agent={agent_flag}")

    start = time.time()
    body = await request.json()
    features_batch = body.get("inputs", [])

    if not features_batch:
        logging.warning(f"[Model] Empty input batch | TXID={txid}")
        return {"error": "Empty input batch", "prediction": [], "metrics": {}}

    # Confidence variance stub (simulate confidence scores)
    confidences = [0.85 + 0.1 * np.random.rand() for _ in features_batch]
    confidence_variance = float(np.var(confidences)) if confidences else 0.0

    # ✅ Derive labels and predictions based on rainfall thresholds
    derived_labels = []
    aligned_predictions = []
    for features, conf in zip(features_batch, confidences):
        rainfall = features[0]
        if rainfall < 70:
            label = "flood_risk_low"
        elif rainfall < 140:
            label = "flood_risk_medium"
        else:
            label = "flood_risk_high"

        normalized_label = normalize_label(label)
        derived_labels.append(normalized_label)
        aligned_predictions.append({
            "label": normalized_label,
            "confidence": round(conf, 2)
        })

    latency = int((time.time() - start) * 1000)

    recent_data = {
        "features": features_batch,
        "labels": derived_labels,
        "latency": latency,
        "confidence_variance": confidence_variance
    }

    logging.info(f"[MODEL-BUILDER] Payload={recent_data}")
    logging.info(f"[Model] Derived labels: {derived_labels}")

    # ✅ Compute metrics using aligned predictions vs derived labels
    metrics = compute_metrics(aligned_predictions, recent_data)
    metrics = sanitize_metrics(metrics)

    logging.info(f"[Model] Prediction={aligned_predictions} | Latency={latency}ms | Metrics={metrics}")

    logging.info(f"[Model] Prediction: {aligned_predictions} | Latency: {latency}ms | Metrics: {metrics}")

    return {
        "prediction": aligned_predictions,
        "metrics": metrics
        "latency_ms": latency,
        "confidence_variance": confidence_variance
    }
