import json
import time
import logging
import redis
import socket
from datetime import datetime
from kafka import KafkaConsumer
from typing import Any, Dict

# ─────────────────────────────────────────────────────────────
# ✅ Logging setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mms-consumer")
logger.info("[MMS] 🟡 Starting MMS consumer...")

# ─────────────────────────────────────────────────────────────
# ✅ Utilities
# ─────────────────────────────────────────────────────────────
def _to_float(value: Any, default: float) -> float:
    """Cast to float with fallback default for None/empty/invalid values."""
    try:
        v = value if value not in (None, "") else default
        return float(v)
    except Exception:
        return float(default)

def _to_int(value: Any, default: int) -> int:
    """Cast to int with fallback."""
    try:
        v = value if value not in (None, "") else default
        return int(v)
    except Exception:
        return int(default)

# ─────────────────────────────────────────────────────────────
# ✅ Kafka availability wait loop
# ─────────────────────────────────────────────────────────────
def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                logger.info("[MMS] ✅ Kafka is available.")
                return
        except OSError:
            if time.time() - start > timeout:
                logger.error("[MMS] ❌ Timeout: Kafka not available.")
                raise TimeoutError("Kafka not available after timeout.")
            logger.info("[MMS] ⏳ Waiting for Kafka...")
            time.sleep(2)

# ─────────────────────────────────────────────────────────────
# ✅ Safe deserializer for Kafka messages
# ─────────────────────────────────────────────────────────────
def safe_deserializer(m):
    try:
        return json.loads(m.decode("utf-8"))
    except Exception as e:
        logger.error(f"[MMS] ❌ Failed to deserialize message: {e}")
        return {}

# ─────────────────────────────────────────────────────────────
# ✅ Extract metrics from payload (pass-through with defaults)
# ─────────────────────────────────────────────────────────────
def extract_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    metrics = payload.get("metrics", {}) or {}
    return {
        "accuracy": metrics.get("accuracy", 0.0),
        "f1_score": metrics.get("f1_score", 0.0),
        "confidence_variance": metrics.get("confidence_variance", 0.0),
        "rmse": metrics.get("rmse", None),
        "feature_drift": metrics.get("feature_drift", None),
        "domain_violation_count": metrics.get("domain_violation_count", None),
        "failure_rate": metrics.get("model_failure_rate", None),
        "watts_per_inference": payload.get("system_power_w", None),
        "confidence_floor": metrics.get("confidence_floor", None)
    }

# ─────────────────────────────────────────────────────────────
# ✅ Main execution block
# ─────────────────────────────────────────────────────────────
def main():
    wait_for_kafka()

    TOPIC = "live_model_metrics"
    BOOTSTRAP_SERVERS = ["kafka:9092"]

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=safe_deserializer,
        auto_offset_reset="earliest",
        group_id="mms-consumer-group",
        client_id="mms-consumer-client"
    )

    logger.info("[MMS] 🔄 Kafka consumer initialized. Waiting for telemetry...")

    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

    for message in consumer:
        try:
            payload = message.value
            if not payload:
                logger.warning("[MMS] ⚠️ Skipping empty or invalid payload")
                continue

            # 🔎 Log raw payload and keys
            logger.info(f"[MMS] 📥 RAW payload={payload}")
            logger.info(f"[MMS] 📥 Payload keys={list(payload.keys())}")

            model_id = payload.get("model_id", "unknown-model")
            txid = payload.get("txid_hash", "no-txid")
            logger.info(f"[MMS] 📥 Received telemetry | TXID={txid} | Model={model_id}")

            # 🔎 Extract metrics
            metrics = extract_metrics(payload)
            logger.info(f"[MMS] 🔎 Extracted metrics (raw)={metrics}")

            # 🔎 Log types before casting
            logger.info(
                "[MMS] 🔎 Raw types | "
                f"accuracy={type(metrics.get('accuracy'))}, "
                f"f1_score={type(metrics.get('f1_score'))}, "
                f"rmse={type(metrics.get('rmse'))}, "
                f"feature_drift={type(metrics.get('feature_drift'))}, "
                f"domain_violation_count={type(metrics.get('domain_violation_count'))}, "
                f"failure_rate={type(metrics.get('failure_rate'))}, "
                f"watts_per_inference={type(metrics.get('watts_per_inference'))}, "
                f"confidence_floor={type(metrics.get('confidence_floor'))}, "
                f"confidence_variance={type(metrics.get('confidence_variance'))}"
            )

            # ✅ Defensive casting
            casted = {
                "accuracy": _to_float(metrics.get("accuracy"), 0.0),
                "f1_score": _to_float(metrics.get("f1_score"), 0.0),
                "confidence_variance": _to_float(metrics.get("confidence_variance"), 0.0),
                "rmse": _to_float(metrics.get("rmse"), 0.0) if metrics.get("rmse") is not None else None,
                "feature_drift": _to_float(metrics.get("feature_drift"), 0.0) if metrics.get("feature_drift") is not None else None,
                "domain_violation_count": _to_int(metrics.get("domain_violation_count"), 0) if metrics.get("domain_violation_count") is not None else 0,
                "failure_rate": _to_float(metrics.get("failure_rate"), 0.0) if metrics.get("failure_rate") is not None else 0.0,
                "watts_per_inference": _to_float(metrics.get("watts_per_inference"), 0.0) if metrics.get("watts_per_inference") is not None else 0.0,
                "confidence_floor": _to_float(metrics.get("confidence_floor"), 0.0) if metrics.get("confidence_floor") is not None else 0.0
            }

            logger.info(f"[MMS] 🔎 Casted metrics={casted}")

            # ✅ Redis keys
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%SZ")
            redis_key_latest = f"metrics:{model_id}"
            redis_key_historical = f"{redis_key_latest}:{timestamp}"

            redis_value = json.dumps({
                "timestamp": timestamp,
                "metrics": casted
            })

            # ✅ Store metrics
            r.set(redis_key_latest, redis_value)
            r.set(redis_key_historical, redis_value)
            r.set(f"{redis_key_latest}:accuracy", casted["accuracy"])
            r.set(f"{redis_key_latest}:f1_score", casted["f1_score"])

            logger.info(
                f"[MMS] ✅ Redis write complete | "
                f"Latest exists={bool(r.exists(redis_key_latest))} | "
                f"Historical exists={bool(r.exists(redis_key_historical))}"
            )
            logger.info(f"[MMS] 📦 Keys stored: {redis_key_latest}, {redis_key_historical}")

        except Exception as e:
            logger.error(f"[MMS] ❌ Error processing message: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[MMS] ❌ Fatal startup error: {e}")
