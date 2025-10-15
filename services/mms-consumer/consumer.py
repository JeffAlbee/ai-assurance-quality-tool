import json
import time
import pickle
import traceback
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

MODEL_PATH = "BridgeTypeModel.pkl"
BOOTSTRAP_SERVERS = "kafka:9092"
INPUT_TOPIC = "live_model_metrics"
OUTPUT_TOPIC = "scored_model_metrics"
GROUP_ID = "mms-consumer"

# Hardcoded baseline for demo
BASELINE = {
    "bridge_type_encoded": {"min": 0, "max": 3},
    "span_length_m": {"min": 10, "max": 100},
    "expected_prediction": "safe"
}

def check_baseline(features, prediction):
    violations = []

    if not (BASELINE["bridge_type_encoded"]["min"] <= features[0] <= BASELINE["bridge_type_encoded"]["max"]):
        violations.append("bridge_type_encoded out of range")

    if not (BASELINE["span_length_m"]["min"] <= features[1] <= BASELINE["span_length_m"]["max"]):
        violations.append("span_length_m out of range")

    if prediction != BASELINE["expected_prediction"]:
        violations.append(f"prediction mismatch: expected {BASELINE['expected_prediction']}, got {prediction}")

    return violations

# Load model
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    model_version = getattr(model, "version", "unknown")
except Exception as e:
    print("[MMS] ❌ Model load failed:", e)
    exit(1)

# Connect to Kafka
for attempt in range(10):
    try:
        consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda m: json.dumps(m).encode("utf-8")
        )
        break
    except NoBrokersAvailable:
        time.sleep(5)
else:
    print("[MMS] ❌ Kafka connection failed.")
    exit(1)

print("[MMS] ✅ Consumer loop started.")

for msg in consumer:
    try:
        telemetry = msg.value
        txid = telemetry.get("txid", "unknown")
        bridge_type = telemetry.get("bridge_type_encoded")
        span_length = telemetry.get("span_length_m")
        features = [bridge_type, span_length]

        if None in features:
            print(f"[MMS] ⚠️ Missing features for txid: {txid}")
            continue

        prediction = model.predict([features])[0]
        violations = check_baseline(features, prediction)

        label = {
            "txid": txid,
            "model_version": model_version,
            "features": {
                "bridge_type_encoded": bridge_type,
                "span_length_m": span_length
            },
            "prediction": prediction,
            "baseline_expected": BASELINE["expected_prediction"],
            "violations": violations,
            "timestamp": time.time()
        }

        producer.send(OUTPUT_TOPIC, label)
        print(f"[MMS] ✅ Scored {txid} → {prediction} | Violations: {len(violations)}")

    except Exception as e:
        print(f"[MMS] ❌ Error processing txid: {txid}")
        traceback.print_exc()
