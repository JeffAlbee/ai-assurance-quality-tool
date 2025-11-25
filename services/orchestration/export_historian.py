import os
import json
from datetime import datetime, timedelta
import redis
from services.mms_api.mms_api.utils.redis_utils import get_old_redis_entries
from db import SessionLocal, insert_archived_violation

# ─────────────────────────────────────────────────────────────
# ✅ Daily Metric Logger (uses live Redis values)
# ─────────────────────────────────────────────────────────────
def log_daily_metrics(model_id, thresholds):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # Pull latest metrics from Redis
    raw = r.get(f"metrics:{model_id}")
    if not raw:
        print(f"⚠️ No metrics found for {model_id}")
        return

    try:
        parsed = json.loads(raw)
        metrics = parsed.get("metrics", {})
    except Exception as e:
        print(f"❌ Failed to parse metrics for {model_id}: {e}")
        return

    violations = []
    for metric, value in metrics.items():
        threshold = thresholds.get(metric)
        if threshold is None or value is None:
            continue
        if metric == "latency" or metric.endswith("_rate") or metric.endswith("_score") or metric == "confidence_variance":
            if value > threshold:
                violations.append({"metric": metric, "type": "max", "value": value, "threshold": threshold})
        else:
            if value < threshold:
                violations.append({"metric": metric, "type": "min", "value": value, "threshold": threshold})

    key = f"metrics:{model_id}:{timestamp}"
    r.set(key, json.dumps({
        "timestamp": timestamp,
        "metrics": metrics,
        "violations": violations
    }))
    print(f"✅ Logged daily metrics for {model_id} at {timestamp}")

# ─────────────────────────────────────────────────────────────
# ✅ Export Redis History to JSON
# ─────────────────────────────────────────────────────────────
def export_model_history(model_id, export_dir):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    keys = sorted(r.keys(f"metrics:{model_id}:*"))

    os.makedirs(export_dir, exist_ok=True)
    filename = f"{model_id}_history_{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(export_dir, filename)

    with open(filepath, "w") as f:
        for key in keys:
            entry = r.get(key)
            try:
                f.write(json.dumps({key: json.loads(entry)}, indent=2) + "\n")
            except Exception as e:
                print(f"⚠️ Failed to export key {key}: {e}")

    print(f"📦 Exported {len(keys)} entries for {model_id} to {filepath}")

# ─────────────────────────────────────────────────────────────
# ✅ Archive Redis → PostgreSQL (30+ days)
# ─────────────────────────────────────────────────────────────
def archive_old_violations(model_id, cutoff_days=30):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    session = SessionLocal()
    archived = 0

    old_entries = get_old_redis_entries(model_id, cutoff_days)
    for key, ts, entry in old_entries:
        for v in entry.get("violations", []):
            insert_archived_violation(session, model_id, ts, v)
        r.delete(key)
        archived += 1

    session.commit()
    session.close()
    print(f"🗃️ Archived {archived} entries for {model_id} to PostgreSQL")

# ─────────────────────────────────────────────────────────────
# ✅ Main Scheduler
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with open("model_config.json") as f:
        config = json.load(f)

    for model in config["models"]:
        model_id = model["model_id"]
        export_dir = model["export_path"]
        thresholds = model.get("thresholds", {})

        log_daily_metrics(model_id, thresholds)
        export_model_history(model_id, export_dir)
        archive_old_violations(model_id)
