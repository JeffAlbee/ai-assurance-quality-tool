print("✅ app.py loaded")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
import logging
import redis
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# ✅ Route Imports (simplified for container context)
# ─────────────────────────────────────────────────────────────
from mms_api.routes.config import router as config_router
from mms_api.routes.exports import router as exports_router
from mms_api.routes.tolerances import router as tolerances_router
from mms_api.routes.violations import router as violations_router
from mms_api.routes.labels import router as labels_router
from mms_api.routes.license import router as license_router
from mms_api.routes.history import router as history_router

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI Initialization
# ─────────────────────────────────────────────────────────────
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# ✅ CORS Middleware
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# ✅ Redis Connection
# ─────────────────────────────────────────────────────────────
try:
    REDIS_HOST = "redis"
    REDIS_PORT = 6379
    REDIS_DB = 0
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    r.ping()
    app.state.redis = r
    logging.info("✅ Connected to Redis")
except Exception as e:
    logging.error(f"❌ Redis connection failed: {e}")
    app.state.redis = None

# ─────────────────────────────────────────────────────────────
# ✅ Route Registration
# ─────────────────────────────────────────────────────────────
app.include_router(config_router)
app.include_router(exports_router)
app.include_router(tolerances_router, prefix="/v1/model")
app.include_router(violations_router, prefix="/v1/model/violations")
app.include_router(labels_router, prefix="/v1/labels")
app.include_router(license_router, prefix="/v1/license")
app.include_router(history_router, prefix="/v1/history")
logging.info("✅ All routers registered")

# 🔍 Print all registered routes with methods and handlers
def list_routes(app: FastAPI):
    print("\n📍 Registered FastAPI Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            print(f"{methods:10} {route.path:30} → {route.endpoint.__name__}")
    print(f"\n✅ Total routes registered: {len(app.routes)}")

list_routes(app)

# ─────────────────────────────────────────────────────────────
# ✅ GET / → Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    logging.info("[MMS-API] 🟢 Health check requested")
    return {"status": "MMS API is running"}

# ─────────────────────────────────────────────────────────────
# ✅ GET /metrics → All Models
# ─────────────────────────────────────────────────────────────
@app.get("/metrics")
def get_all_metrics():
    redis_conn = app.state.redis
    if not redis_conn:
        return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

    logging.info("[MMS-API] 🔍 Fetching all model metrics from Redis")
    all_keys = redis_conn.keys("metrics:*")
    all_metrics = {}

    for key in all_keys:
        parts = key.split(":")
        if len(parts) == 2:
            model_id = parts[1]
            raw = redis_conn.get(key)
            try:
                all_metrics[model_id] = json.loads(raw)
            except Exception as e:
                logging.warning(f"[MMS-API] ⚠️ Failed to parse metrics for {model_id}: {e}")

    return all_metrics

# ─────────────────────────────────────────────────────────────
# ✅ GET /metrics/{model_id} → Specific Model
# ─────────────────────────────────────────────────────────────
@app.get("/metrics/{model_id}")
def get_model_metrics(model_id: str):
    redis_conn = app.state.redis
    if not redis_conn:
        return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

    logging.info(f"[MMS-API] 🔍 Fetching metrics for model: {model_id}")
    raw = redis_conn.get(f"metrics:{model_id}")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            logging.error(f"[MMS-API] ❌ JSON decode error for {model_id}: {e}")
            return {"error": "Failed to decode metrics"}
    else:
        return {"error": "Model not found"}

# ─────────────────────────────────────────────────────────────
# ✅ GET /v1/exports/download → File Export
# ─────────────────────────────────────────────────────────────
@app.get("/v1/exports/download")
def download_export(model_id: str, filename: str):
    try:
        with open("model_config.json") as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"[MMS-API] ❌ Failed to read model_config.json: {e}")
        return {"error": "Configuration file not found or invalid"}

    model = next((m for m in config.get("models", []) if m["model_id"] == model_id), None)
    if not model:
        return {"error": "Model not found"}

    export_dir = model.get("export_path")
    filepath = os.path.join(export_dir, filename)

    if not os.path.exists(filepath):
        return {"error": "File not found"}

    return FileResponse(path=filepath, filename=filename, media_type="application/json")
