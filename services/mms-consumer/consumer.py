import json
import joblib
from kafka import KafkaConsumer

# Kafka topic and broker
TOPIC = "live_model_metrics"
BOOTSTRAP_SERVERS = ["kafka:9092"]

# Try loading the model
try:
    model = joblib.load("BridgeTypeModel.pkl")
    print("[MMS] ✅ Model loaded successfully.")
except FileNotFoundError:
    print("[MMS] ⚠️ BridgeTypeModel.pkl not found. Using default prediction.")
    model = None

# Initialize Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id="mms-consumer-group"
)

print("[MMS] 🔄 Waiting for messages...")

# Message processing loop
for message in consumer:
    payload = message.value
    txid = payload.get("txid")
    features = payload.get("features", [])

    print(f"[MMS] 📥 Received telemetry: TXID={txid}, Features={features}")

    # Predict or fallback
    if model:
        try:
            prediction = model.predict([features])[0]
        except Exception as e:
            print(f"[MMS] ❌ Prediction error: {e}")
            prediction = 0
    else:
        prediction = 0  # Default label for demo

    # Log result
    print(f"[MMS] ✅ TXID={txid} | Label={prediction}")