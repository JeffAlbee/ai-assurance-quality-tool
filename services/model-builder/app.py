from fastapi import FastAPI, Request
from pydantic import BaseModel
from model import predict
from metrics import compute_metrics
import time
import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

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
    maxBytes=5_000_000,  # 5MB per file
    backupCount=3        # Keep 3 rotated logs
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI App Initialization
# ─────────────────────────────────────────────────────────────
app = FastAPI()

# ─────────────────────────────────────────────────────────────
# ✅ Input Schema
# ─────────────────────────────────────────────────────────────
class InputFeatures(BaseModel):
    feature_1: float
    feature_2: float
    # Extend with additional features if needed

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

    logging.info(f"[Model] Inference request received | TXID: {txid} | Model-ID: {model_id} | Sidecar-Agent: {agent_flag}")

    start = time.time()
    input_data = await request.json()
    result = predict(input_data)
    latency = int((time.time() - start) * 1000)

    metrics = compute_metrics()
    metrics["p95_latency"] = latency

    logging.info(f"[Model] Prediction: {result} | Latency: {latency}ms | Metrics: {metrics}")

    return {
        "prediction": result,
        "metrics": metrics
    }
