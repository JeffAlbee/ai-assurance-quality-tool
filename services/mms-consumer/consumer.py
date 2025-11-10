import json
import time
import logging
import redis
import socket
from datetime import datetime
from kafka import KafkaConsumer

# ─────────────────────────────────────────────────────────────
# ✅ Logging Setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mms-consumer")
logger.info("[MMS] 🟡 Starting MMS consumer...")

# ─────────────────────────────────────────────────────────────
# ✅ Kafka Availability Wait Loop
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
# ✅ Safe Deserializer for Kafka Messages
# ─────────────────────────────────────────────────────────────
def safe_deserializer(m):
    try:
        return json.loads(m.decode("utf-8"))
    except Exception as e:
        logger.error(f"[MMS] ❌ Failed to deserialize message: {e}")
        return {}

# ─────────────────────────────────────────────────────────────
# ✅ Extract Metrics from Payload
# ─────────────────────────────────────────────────────────────
def extract_metrics(payload):
    metrics = payload.get("metrics", {})
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
# ✅ Main Execution Block
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

            model_id = payload.get("model_id", "unknown-model")
            txid = payload.get("txid_hash", "no-txid")

            logger.info(f"[MMS] 📥 Received telemetry | TXID={txid} | Model={model_id}")

            metrics = extract_metrics(payload)

            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%SZ")
            redis_key_latest = f"metrics:{model_id}"
            redis_key_historical = f"{redis_key_latest}:{timestamp}"

            redis_value = json.dumps({
                "timestamp": timestamp,
                "metrics": metrics
            })

            # ✅ Store full metric payload
            r.set(redis_key_latest, redis_value)
            r.set(redis_key_historical, redis_value)

            # ✅ Store accuracy and F1 separately for Grafana or alerting
            r.set(f"{redis_key_latest}:accuracy", metrics["accuracy"])
            r.set(f"{redis_key_latest}:f1_score", metrics["f1_score"])

            logger.info(f"[MMS] ✅ Redis write complete | Latest: {r.exists(redis_key_latest)} | Historical: {r.exists(redis_key_historical)}")
            logger.info(f"[MMS] 📦 Keys stored: {redis_key_latest}, {redis_key_historical}")
        except Exception as e:
            logger.error(f"[MMS] ❌ Error processing message: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"[MMS] ❌ Fatal startup error: {e}")
