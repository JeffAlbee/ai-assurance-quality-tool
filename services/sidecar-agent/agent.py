import time
import uuid
import hashlib
import requests
import json
import logging
import os

# ─────────────────────────────────────────────────────────────
# ✅ Logging Setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ─────────────────────────────────────────────────────────────
# ✅ Configurable Settings
# ─────────────────────────────────────────────────────────────
TIB_URL = os.getenv("TIB_URL", "http://tib-producer-api:8002/ingest")
ASSURANCE_URL = os.getenv("ASSURANCE_URL", "http://assurance-service:8000/v1/labels")
MODEL_ID = os.getenv("MODEL_ID", "flood-risk-predictor")
SYSTEM_POWER_W = float(os.getenv("SYSTEM_POWER_W", "42.0"))

# ─────────────────────────────────────────────────────────────
# ✅ Dummy Model (Replace with real model later)
# ─────────────────────────────────────────────────────────────
class DummyModel:
    def predict(self, input_data):
        return {
            "prediction": "flood_risk_high",
            "confidence": 0.92,
            "attribution": [
                {"feature": "rainfall_mm", "score": 0.6},
                {"feature": "bridge_type_encoded", "score": 0.3}
            ]
        }

# ─────────────────────────────────────────────────────────────
# ✅ Step 1: Capture Inference
# ─────────────────────────────────────────────────────────────
def capture_inference(model, input_data):
    start_time = time.time()
    output_data = model.predict(input_data)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "input": input_data,
        "output": output_data,
        "latency_ms": latency_ms,
        "confidence": output_data.get("confidence"),
        "attribution": output_data.get("attribution", [])
    }

# ─────────────────────────────────────────────────────────────
# ✅ Step 2: Build Full Telemetry Payload
# ─────────────────────────────────────────────────────────────
def build_payload(model_id, inference_data):
    txid = str(uuid.uuid4())
    input_data = inference_data["input"]
    output_data = inference_data["output"]

    payload = {
        "txid": txid,
        "model_id": model_id,
        "inference_timestamp": int(time.time() * 1000),
        "request_payload": input_data,
        "response_payload": output_data,
        "ground_truth": None,
        "system_power_w": SYSTEM_POWER_W,
        "confidence_score": inference_data["confidence"],
        "attribution_vector": inference_data["attribution"],
        "features": [
            input_data.get("rainfall_mm", 0.0),
            input_data.get("bridge_type_encoded", 0)
        ]
    }

    payload_str = json.dumps(payload, sort_keys=True)
    payload["txid_hash"] = hashlib.sha256(payload_str.encode()).hexdigest()

    return payload

# ─────────────────────────────────────────────────────────────
# ✅ Step 3a: Send to TIB Producer API
# ─────────────────────────────────────────────────────────────
def send_to_tib(payload, retries=10, delay=3):
    for attempt in range(retries):
        try:
            response = requests.post(TIB_URL, json=payload)
            logging.info(f"[Sidecar] Telemetry sent to TIB: {payload['txid_hash']} | Status: {response.status_code}")
            return
        except Exception as e:
            logging.warning(f"[Sidecar] Attempt {attempt+1} failed: {e}")
            time.sleep(delay)
    logging.error("[Sidecar] Failed to send telemetry to TIB after retries.")

# ─────────────────────────────────────────────────────────────
# ✅ Step 3b: Send to Assurance Service
# ─────────────────────────────────────────────────────────────
def send_to_assurance(payload):
    label = {
        "txid": payload["txid"],
        "model_id": payload["model_id"],
        "prediction": payload["response_payload"]["prediction"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    try:
        response = requests.post(ASSURANCE_URL, json=label)
        logging.info(f"[Sidecar] Label sent to assurance-service: {label['txid']} | Status: {response.status_code}")
    except Exception as e:
        logging.error(f"[Sidecar] Failed to send label to assurance-service: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Step 4: Main Execution Block
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    model = DummyModel()
    input_data = {
        "rainfall_mm": 85.2,
        "bridge_type_encoded": 3
    }

    inference_data = capture_inference(model, input_data)
    payload = build_payload(MODEL_ID, inference_data)

    send_to_tib(payload)
    send_to_assurance(payload)
