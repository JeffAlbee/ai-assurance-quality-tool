from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json, time

app = FastAPI()

# Define the expected telemetry schema
class TelemetryPayload(BaseModel):
    model_id: str
    inference_timestamp: int
    request_payload: dict
    response_payload: dict
    ground_truth: dict | None = None
    system_power_w: float
    confidence_score: float
    attribution_vector: list[dict]
    features: list[float]  # ✅ Required for MMS scoring
    txid_hash: str

# Initialize Kafka producer with retry logic
def init_kafka_producer(retries=10, delay=2):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print("[TIB] Kafka producer initialized.")
            return producer
        except Exception as e:
            print(f"[TIB] Kafka producer init failed (attempt {attempt+1}): {e}")
            time.sleep(delay)
    print("[TIB] Kafka producer failed after retries.")
    return None

producer = init_kafka_producer()

# Ingest endpoint
@app.post("/ingest")
def ingest(payload: TelemetryPayload):
    print(f"\n[TIB] --- Incoming Telemetry ---")
    print(f"[TIB] TXID: {payload.txid_hash}")
    print(f"[TIB] Full Payload: {json.dumps(payload.dict(), indent=2)}")

    if not producer:
        raise HTTPException(status_code=500, detail="Kafka producer unavailable")

    try:
        producer.send("live_model_metrics", value=payload.dict())
        producer.flush()
        print(f"[TIB] ✅ Telemetry forwarded: {payload.txid_hash}")
        return {"status": "success", "txid_hash": payload.txid_hash}
    except Exception as e:
        print(f"[TIB] ❌ Failed to forward telemetry: {e}")
        raise HTTPException(status_code=500, detail="Telemetry forwarding failed")
