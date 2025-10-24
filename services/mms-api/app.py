from fastapi import FastAPI
from typing import Dict
import logging
import redis
import json

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI Initialization
# ─────────────────────────────────────────────────────────────
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# ✅ Redis Connection
# ─────────────────────────────────────────────────────────────
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# ─────────────────────────────────────────────────────────────
# ✅ GET / → Health Check for Grafana
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    logging.info("[MMS-API] 🟢 Health check requested")
    return {"status": "MMS API is running"}

# ─────────────────────────────────────────────────────────────
# ✅ GET /metrics → All Models
# ─────────────────────────────────────────────────────────────
@app.get("/metrics")
def get_all_metrics():
    logging.info("[MMS-API] 🔍 Fetching all model metrics from Redis")
    all_keys = r.keys("metrics:*")
    all_metrics = {}

    for key in all_keys:
        model_id = key.split(":")[1]
        raw = r.get(key)
        try:
            all_metrics[model_id] = json.loads(raw)
        except Exception as e:
            logging.warning(f"[MMS-API] ⚠️ Failed to parse metrics for {model_id}: {e}")

    return all_metrics

# ─────────────────────────────────────────────────────────────
# ✅ GET /metrics/{model_id} → Specific Model
# ─────────────────────────────────────────────────────────────
@app.get("/metrics/{model_id}")
def get_model_metrics(model_id: str):
    logging.info(f"[MMS-API] 🔍 Fetching metrics for model: {model_id}")
    raw = r.get(f"metrics:{model_id}")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            logging.error(f"[MMS-API] ❌ JSON decode error for {model_id}: {e}")
            return {"error": "Failed to decode metrics"}
    else:
        return {"error": "Model not found"}
