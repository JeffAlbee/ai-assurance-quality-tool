import time
import redis
import logging
from datetime import datetime, timezone
import os
import sys

# Dynamically add model-builder to path
MODEL_BUILDER_PATH = os.path.join(os.path.dirname(__file__), "model-builder")
sys.path.append(MODEL_BUILDER_PATH)

from metrics import compute_metrics
from model import load_model
from data import fetch_recent_data

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# ✅ Redis Connection
# ─────────────────────────────────────────────────────────────
try:
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    r.ping()
    logging.info("✅ Connected to Redis")
except Exception as e:
    logging.error(f"❌ Redis connection failed: {e}")
    exit(1)

# ─────────────────────────────────────────────────────────────
# ✅ Streaming Loop
# ─────────────────────────────────────────────────────────────
def stream_metrics(model_id: str, model):
    logging.info(f"🚀 Starting metric stream for model: {model_id}")
    while True:
        try:
            recent_data = fetch_recent_data()
            metrics = compute_metrics(model, recent_data)

            # ⏱️ Millisecond timestamp for RedisTimeSeries
            ts = int(datetime.now(timezone.utc).timestamp() * 1000)

            # 🔁 Write each metric to its own RedisTimeSeries key
            r.execute_command("TS.ADD", f"metrics:{model_id}:accuracy", ts, metrics["accuracy"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:rmse", ts, metrics["rmse"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:feature_drift", ts, metrics["feature_drift"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:domain_violation_count", ts, metrics["domain_violation_count"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:p95_latency", ts, metrics["p95_latency"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:failure_rate", ts, metrics["failure_rate"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:watts_per_inference", ts, metrics["watts_per_inference"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:confidence_floor", ts, metrics["confidence_floor"])
            r.execute_command("TS.ADD", f"metrics:{model_id}:confidence_variance", ts, metrics["confidence_variance"])

            logging.info(f"✅ Streamed metrics for {model_id} at {ts}")
        except Exception as e:
            logging.error(f"❌ Failed to stream metrics for {model_id}: {e}")

        time.sleep(300)  # ⏱️ Log every 5 minutes

# ─────────────────────────────────────────────────────────────
# ✅ Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model_id = "flood-risk-model"
    model = load_model(model_id)
    stream_metrics(model_id, model)
