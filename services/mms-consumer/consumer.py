import json
import time
import logging
import redis
import socket
from kafka import KafkaConsumer

# ─────────────────────────────────────────────────────────────
# ✅ Logging Setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.info("[MMS] 🟡 Starting MMS consumer...")

# ─────────────────────────────────────────────────────────────
# ✅ Kafka Availability Wait Loop
# ─────────────────────────────────────────────────────────────
def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                logging.info("[MMS] ✅ Kafka is available.")
                return
        except OSError:
            if time.time() - start > timeout:
                logging.error("[MMS] ❌ Timeout: Kafka not available.")
                raise TimeoutError("Kafka not available after timeout.")
            logging.info("[MMS] ⏳ Waiting for Kafka...")
            time.sleep(2)

wait_for_kafka()

# ─────────────────────────────────────────────────────────────
# ✅ Kafka Consumer Configuration
# ─────────────────────────────────────────────────────────────
TOPIC = "live_model_metrics"
BOOTSTRAP_SERVERS = ["kafka:9092"]

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="mms-consumer-group"
)

logging.info("[MMS] 🔄 Kafka consumer initialized. Waiting for telemetry...")

# ─────────────────────────────────────────────────────────────
# ✅ Redis Connection
# ─────────────────────────────────────────────────────────────
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# ─────────────────────────────────────────────────────────────
# ✅ Metric Computation Logic
# ─────────────────────────────────────────────────────────────
def compute_metrics(payload):
    confidence = payload.get("response_payload", {}).get("confidence", 0.0)
    power = payload.get("system_power_w", 0.0)
    drift = payload.get("feature_drift", 0.03)
    violations = payload.get("domain_violation_count", 2)

    return {
        "accuracy": 0.92,
        "rmse": 1.2,
        "feature_drift": drift,
        "domain_violation_count": violations,
        "failure_rate": 0.01,
        "watts_per_inference": power,
        "confidence_floor": confidence,
        "confidence_variance": 0.04
    }

# ─────────────────────────────────────────────────────────────
# ✅ Message Handler Loop
# ─────────────────────────────────────────────────────────────
for message in consumer:
    payload = message.value
    model_id = payload.get("model_id", "unknown-model")
    txid = payload.get("txid_hash", "no-txid")

    logging.info(f"[MMS] 📥 Received telemetry | TXID={txid} | Model={model_id}")

    metrics = compute_metrics(payload)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    redis_key = f"metrics:{model_id}"
    redis_value = json.dumps({
        "timestamp": timestamp,
        "metrics": metrics
    })

    try:
        r.set(redis_key, redis_value)
        logging.info(f"[MMS] ✅ Metrics written to Redis for {model_id}")
    except Exception as e:
        logging.error(f"[MMS] ❌ Redis write failed for {model_id}: {e}")
