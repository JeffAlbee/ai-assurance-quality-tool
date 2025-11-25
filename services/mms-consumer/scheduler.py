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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

logging.info(f"📂 Current working directory: {BASE_DIR}")
if os.path.exists(MODEL_BUILDER_PATH):
    logging.info(f"📂 Contents of model-builder: {os.listdir(MODEL_BUILDER_PATH)}")
else:
    logging.warning(f"⚠️ model-builder directory not found at {MODEL_BUILDER_PATH}. Skipping listing.")

# ─────────────────────────────────────────────────────────────
# ✅ Imports from model-builder
# ─────────────────────────────────────────────────────────────
try:
    sys.path.append(MODEL_BUILDER_PATH)
    from model import load_model
    from data import fetch_recent_data
except ModuleNotFoundError as e:
    logging.error(f"❌ Import failed from model-builder: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# ✅ Imports from orchestration
# ─────────────────────────────────────────────────────────────
try:
    from orchestration.utils.redis_utils import get_old_redis_entries, get_redis_client
except ModuleNotFoundError as e:
    logging.warning(f"⚠️ Archival module not found: {e}")
    get_old_redis_entries = None
    get_redis_client = None

# ─────────────────────────────────────────────────────────────
# ✅ Metric Computation
# ─────────────────────────────────────────────────────────────
def compute_metrics(model, data_batch):
    try:
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
    except Exception as e:
        logging.error(f"❌ Metric computation failed: {e}")
        return {}

# ─────────────────────────────────────────────────────────────
# ✅ Streaming Loop
# ─────────────────────────────────────────────────────────────
def stream_metrics(model_id: str, model):
    r = get_redis_client()
    if not r:
        logging.error("❌ Redis client unavailable. Exiting stream.")
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
# ✅ Archival Logic
# ─────────────────────────────────────────────────────────────
def archive_old_violations(model_id: str):
    r = get_redis_client()
    if not r or not get_old_redis_entries:
        logging.error("❌ Archival prerequisites not met. Skipping archival.")
        return

    old_entries = get_old_redis_entries(model_id)
    for key, ts, entry in old_entries:
        try:
            archived_key = f"archived:{key}"
            r.rename(key, archived_key)
            logging.info(f"🧹 Archived key: {key} → {archived_key} (timestamp: {ts})")
        except Exception as e:
            logging.warning(f"⚠️ Failed to archive key {key}: {e}")

def run_daily_archival():
    try:
        with open(MODEL_CONFIG_PATH) as f:
            config = json.load(f)
            model_id = config["models"][0]["model_id"]
            logging.info(f"📦 Running archival for model: {model_id}")
            archive_old_violations(model_id)
            logging.info("✅ Archival completed")
    except FileNotFoundError:
        logging.error(f"❌ model_config.json not found at {MODEL_CONFIG_PATH}")
    except Exception as e:
        logging.error(f"❌ Archival failed: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📄 Attempting to load config from: {MODEL_CONFIG_PATH}")
    if len(sys.argv) > 1 and sys.argv[1] == "archive":
        run_daily_archival()
    else:
        try:
            with open(MODEL_CONFIG_PATH) as f:
                config = json.load(f)
                model_id = config["models"][0]["model_id"]
                model = load_model(model_id)
                stream_metrics(model_id, model)
        except Exception as e:
            logging.error(f"❌ Scheduler failed to start: {e}")
