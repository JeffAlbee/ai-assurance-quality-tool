print("✅ tolerances.py loaded")

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import logging

router = APIRouter()

print("✅ /ping route defined")

# ─────────────────────────────────────────────────────────────
# ✅ Health Check Route (registered first)
# ─────────────────────────────────────────────────────────────
@router.get("/ping", tags=["tolerances"])
def ping():
    return {"status": "tolerances router is active"}

# ─────────────────────────────────────────────────────────────
# ✅ Redis Access Helper
# ─────────────────────────────────────────────────────────────
def get_redis(request: Request):
    r = request.app.state.redis
    if not r:
        raise RuntimeError("Redis connection not available")
    return r

# ─────────────────────────────────────────────────────────────
# ✅ POST /tolerances → Save Validated Tolerances
# ─────────────────────────────────────────────────────────────
@router.post("/tolerances")
async def save_tolerances(request: Request):
    try:
        data = await request.json()
        model_id = data.get("model_id")
        tolerances = data.get("tolerances")

        if not model_id or not isinstance(tolerances, dict):
            return JSONResponse(status_code=400, content={"error": "Missing or invalid model_id/tolerances"})

        for metric, bounds in tolerances.items():
            if not isinstance(bounds, dict):
                return {"error": f"Invalid bounds for {metric}"}
            min_val = bounds.get("min")
            max_val = bounds.get("max")
            if min_val is not None and not isinstance(min_val, (int, float)):
                return {"error": f"Min for {metric} must be numeric"}
            if max_val is not None and not isinstance(max_val, (int, float)):
                return {"error": f"Max for {metric} must be numeric"}
            if min_val is not None and max_val is not None and min_val > max_val:
                return {"error": f"Min cannot exceed max for {metric}"}

        r = get_redis(request)
        r.set(f"tolerances:{model_id}", json.dumps(tolerances))
        logging.info(f"[Tolerances] ✅ Saved for {model_id}")
        return {"status": "saved", "model_id": model_id}
    except Exception as e:
        logging.error(f"[Tolerances] ❌ Failed to save tolerances: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

# ─────────────────────────────────────────────────────────────
# ✅ GET /tolerances → Fetch Tolerances
# ─────────────────────────────────────────────────────────────
@router.get("/tolerances")
def get_tolerances(model_id: str, request: Request):
    try:
        r = get_redis(request)
        raw = r.get(f"tolerances:{model_id}")
        if raw:
            return {"model_id": model_id, "tolerances": json.loads(raw)}
        else:
            return {"error": "No tolerances found for model"}
    except Exception as e:
        logging.error(f"[Tolerances] ❌ Failed to fetch tolerances: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

# ─────────────────────────────────────────────────────────────
# ✅ POST /metrics/{model_id} → Ingest + Compare + Log
# ─────────────────────────────────────────────────────────────
@router.post("/metrics/{model_id}")
async def ingest_metrics(model_id: str, request: Request):
    try:
        data = await request.json()
        metrics = data.get("metrics")
        if not metrics or not isinstance(metrics, dict):
            return {"error": "Missing or invalid metrics"}

        for metric, value in metrics.items():
            if not isinstance(value, (int, float)):
                return {"error": f"Metric '{metric}' must be numeric"}

        r = get_redis(request)

        # Save full snapshot
        r.set(f"metrics:{model_id}", json.dumps({
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Flatten for Grafana
        for key, value in metrics.items():
            r.set(f"metrics:{model_id}:{key}", value)

        # Compare to tolerances
        violations = []
        raw_tolerances = r.get(f"tolerances:{model_id}")
        if raw_tolerances:
            try:
                tolerances = json.loads(raw_tolerances)
                for metric, value in metrics.items():
                    rule = tolerances.get(metric, {})
                    if "min" in rule and value < rule["min"]:
                        violations.append({
                            "metric": metric,
                            "type": "min",
                            "value": value,
                            "threshold": rule["min"]
                        })
                    if "max" in rule and value > rule["max"]:
                        violations.append({
                            "metric": metric,
                            "type": "max",
                            "value": value,
                            "threshold": rule["max"]
                        })
            except Exception as e:
                logging.warning(f"[Tolerances] ⚠️ Failed to parse tolerances for {model_id}: {e}")

        # Log violations
        if violations:
            timestamp = datetime.utcnow().isoformat()
            r.set(f"violations:{model_id}:{timestamp}", json.dumps(violations))
            r.lpush(f"violations:{model_id}:recent", json.dumps({
                "timestamp": timestamp,
                "violations": violations
            }))
            logging.warning(f"[Tolerances] 🚨 Violations for {model_id}: {violations}")

        return {"status": "metrics saved", "violations": violations}
    except Exception as e:
        logging.error(f"[Tolerances] ❌ Failed to ingest metrics: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

# ─────────────────────────────────────────────────────────────
# ✅ GET /violations → Fetch Recent Alerts
# ─────────────────────────────────────────────────────────────
@router.get("/violations")
def get_recent_violations(model_id: str, request: Request, limit: int = 100):
    try:
        r = get_redis(request)
        raw_list = r.lrange(f"violations:{model_id}:recent", 0, limit - 1)

        decoded = []
        for item in raw_list:
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict) and "timestamp" in parsed and "violations" in parsed:
                    decoded.append(parsed)
                else:
                    logging.warning(f"[Historian] ⚠️ Skipped malformed entry: {parsed}")
            except Exception as e:
                logging.warning(f"[Historian] ⚠️ Failed to decode violation entry: {e}")
                continue

        logging.info(f"[Historian] ✅ Returned {len(decoded)} violations for {model_id}")
        return decoded
    except Exception as e:
        logging.error(f"[Historian] ❌ Failed to fetch violations: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

__all__ = ["router"]
