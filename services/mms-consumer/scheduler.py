import time
import logging
import os
import sys
import json
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# ✅ Environment Setup
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.getcwd()
MODEL_BUILDER_PATH = os.path.join(BASE_DIR, "model-builder")
MODEL_CONFIG_PATH = "/app/model_config.json"

print(f"📂 Current working directory: {BASE_DIR}")
if os.path.exists(MODEL_BUILDER_PATH):
    print(f"📂 Contents of model-builder: {os.listdir(MODEL_BUILDER_PATH)}")
else:
    print(f"⚠️ model-builder directory not found at {MODEL_BUILDER_PATH}. Skipping listing.")


# ─────────────────────────────────────────────────────────────
# ✅ Imports from model-builder
# ─────────────────────────────────────────────────────────────
try:
    sys.path.append(MODEL_BUILDER_PATH)
    from model import load_model
    from data import fetch_recent_data
except ModuleNotFoundError as e:
    logging.error(f"❌ Import failed: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# ✅ Imports from local modules
# ─────────────────────────────────────────────────────────────
from historian import archive_old_violations

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# ✅ Metric Computation
# ─────────────────────────────────────────────────────────────
def compute_metrics(model, data_batch):
    predictions = model.predict(data_batch)
    confidences = model.confidence(data_batch)

    accuracy = sum(1 for p in predictions if p == "safe") / len(predictions)
    f1_score = 0.75  # Placeholder
    mean_conf = sum(confidences) / len(confidences)
    confidence_variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)

    return {
        "accuracy": round(accuracy, 4),
        "f1_score": round(f1_score, 4),
        "confidence_variance": round(confidence_variance, 4),
        "latency": 320,
        "drift_score": 0.35
    }

# ─────────────────────────────────────────────────────────────
# ✅ Streaming Loop
# ─────────────────────────────────────────────────────────────
def stream_metrics(model_id: str, model):
    import redis
    try:
        r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
        r.ping()
        logging.info("✅ Connected to Redis")
    except Exception as e:
        logging.error(f"❌ Redis connection failed: {e}")
        return

    logging.info(f"🚀 Starting metric stream for model: {model_id}")
    while True:
        try:
            recent_data = fetch_recent_data()
            metrics = compute_metrics(model, recent_data)
            ts = int(datetime.now(timezone.utc).timestamp() * 1000)

            for metric, value in metrics.items():
                r.execute_command("TS.ADD", f"metrics:{model_id}:{metric}", ts, value)

            logging.info(f"✅ Streamed metrics for {model_id} at {ts}")
        except Exception as e:
            logging.error(f"❌ Failed to stream metrics for {model_id}: {e}")

        time.sleep(300)

# ─────────────────────────────────────────────────────────────
# 🚫 Archival Temporarily Disabled
# ─────────────────────────────────────────────────────────────
def run_daily_archival():
    logging.warning("⚠️ Archival mode is temporarily disabled. Skipping run.")



# ─────────────────────────────────────────────────────────────
# ✅ Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "archive":
        run_daily_archival()
    else:
        model_id = "flood-risk-model"
        model = load_model(model_id)
        stream_metrics(model_id, model)
