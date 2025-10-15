from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda m: json.dumps(m).encode("utf-8")
)

with open("sample_payload.json") as f:
    payload = json.load(f)

producer.send("live_model_metrics", payload)
producer.flush()
print("✅ Sample payload sent.")
