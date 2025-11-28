from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from kafka import KafkaProducer
import json, time, logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="[TIB] %(asctime)s %(levelname)s: %(message)s")

app = FastAPI(title="Telemetry Ingest Broker (TIB)")

# Define nested schemas for clarity
class RequestPayload(BaseModel):
    inputs: list

class Prediction(BaseModel):
    label: str
    confidence: float

class ResponsePayload(BaseModel):
    predictions: list[Prediction]
    latency_ms: int
    accuracy: float
    f1_score: float
    confidence_variance: float

class GroundTruth(BaseModel):
    labels: list[str]

# Define the expected telemetry schema
class TelemetryPayload(BaseModel):
    model_id: str
    inference_timestamp: int
    request_payload: RequestPayload
    response_payload: ResponsePayload
    ground_truth: GroundTruth | None = None
    system_power_w: float = Field(..., description="System power consumption in watts")
    confidence_score: float = Field(..., description="Mean confidence across predictions")
    attribution_vector: list[dict] = []
    features: list[float] = Field(default_factory=list, description="Feature vector for MMS scoring")
    txid_hash: str

# Initialize Kafka producer with retry logic
def init_kafka_producer(retries=10, delay=2):
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            logging.info("Kafka producer initialized.")
            return producer
        except Exception as e:
            logging.error(f"Kafka producer init failed (attempt {attempt+1}): {e}")
            time.sleep(delay)
    logging.error("Kafka producer failed after retries.")
    return None

producer = init_kafka_producer()

# Ingest endpoint
@app.post("/ingest")
def ingest(payload: TelemetryPayload):
    logging.info("--- Incoming Telemetry ---")
    logging.info(f"TXID: {payload.txid_hash}")
    logging.debug(f"Full Payload: {json.dumps(payload.dict(), indent=2)}")

    if not producer:
        raise HTTPException(status_code=500, detail="Kafka producer unavailable")

    try:
        producer.send("live_model_metrics", value=payload.dict())
        producer.flush()
        logging.info(f"✅ Telemetry forwarded: {payload.txid_hash}")
        return {"status": "success", "txid_hash": payload.txid_hash}
    except Exception as e:
        logging.error(f"❌ Failed to forward telemetry: {e}")
        raise HTTPException(status_code=500, detail="Telemetry forwarding failed")
