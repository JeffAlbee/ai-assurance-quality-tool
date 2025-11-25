import redis
import logging
import json
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────────────────────
# ✅ Redis Client Initialization
# ─────────────────────────────────────────────────────────────
def get_redis_client():
    try:
        client = redis.Redis(
            host="redis",  # Use "localhost" for local dev; change to "redis" in Docker
            port=6379,
            db=0,
            decode_responses=True
        )
        client.ping()
        logging.info("✅ Redis client connected successfully")
        return client
    except redis.ConnectionError as e:
        logging.error(f"❌ Redis connection failed: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# ✅ Scan and Filter Redis Keys Older Than Cutoff
# ─────────────────────────────────────────────────────────────
def get_old_redis_entries(model_id: str, cutoff_days: int = 30, r=None):
    if r is None:
        r = get_redis_client()
    if not r:
        logging.error("❌ Redis client unavailable for scanning")
        return []

    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=cutoff_days)
    pattern = f"metrics:{model_id}:*"
    old_entries = []

    for key in r.scan_iter(pattern):
        raw = r.get(key)
        if not raw:
            continue
        try:
            entry = json.loads(raw)
            ts_raw = entry.get("timestamp")
            if not ts_raw:
                logging.warning(f"⚠️ Missing timestamp in key {key}")
                continue
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            if ts < cutoff:
                old_entries.append((key, ts, entry))
        except Exception as e:
            logging.warning(f"⚠️ Failed to parse Redis key {key}: {e}")
            continue

    logging.info(f"📦 Found {len(old_entries)} old entries for model: {model_id}")
    return old_entries

# ─────────────────────────────────────────────────────────────
# ✅ Archive Old Keys by Renaming or Deleting
# ─────────────────────────────────────────────────────────────
def archive_keys(model_id: str, cutoff_days: int = 30, action: str = "rename"):
    r = get_redis_client()
    if not r:
        logging.error("❌ Redis client unavailable for archival")
        return

    old_entries = get_old_redis_entries(model_id, cutoff_days, r)
    for key, ts, entry in old_entries:
        try:
            if action == "rename":
                archived_key = f"archived:{key}"
                r.rename(key, archived_key)
                logging.info(f"🧹 Renamed key: {key} → {archived_key}")
            elif action == "delete":
                r.delete(key)
                logging.info(f"🧹 Deleted key: {key}")
            else:
                logging.warning(f"⚠️ Unknown archival action: {action}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to archive key {key}: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Utility: List All Metric Keys for a Model
# ─────────────────────────────────────────────────────────────
def get_metrics_keys(model_id: str):
    r = get_redis_client()
    if not r:
        logging.error("❌ Redis client unavailable for key listing")
        return []
    return list(r.scan_iter(f"metrics:{model_id}:*"))
