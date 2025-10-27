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
# ✅ Metric Computation Logic
# ─────────────────────────────────────────────────────────────
def compute_metrics(payload):
    return {
        "accuracy": 0.92,
        "rmse": 1.2,
        "feature_drift": payload.get("feature_drift", 0.03),
        "domain_violation_count": payload.get("domain_violation_count", 2),
        "failure_rate": 0.01,
        "watts_per_inference": payload.get("system_power_w", 0.0),
        "confidence_floor": payload.get("response_payload", {}).get("confidence", 0.0),
        "confidence_variance": 0.04
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

            metrics = compute_metrics(payload)

            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%SZ")
            redis_key_latest = f"metrics:{model_id}"
            redis_key_historical = f"{redis_key_latest}:{timestamp}"

            redis_value = json.dumps({
                "timestamp": timestamp,
                "metrics": metrics
            })

            r.set(redis_key_latest, redis_value)
            r.set(redis_key_historical, redis_value)

            latest_exists = r.exists(redis_key_latest)
            historical_exists = r.exists(redis_key_historical)

            logger.info(f"[MMS] ✅ Redis write complete | Latest: {latest_exists} | Historical: {historical_exists}")
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
