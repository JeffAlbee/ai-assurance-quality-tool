print("✅ app.py loaded")

# ─────────────────────────────────────────────────────────────
# ✅ Path Debugging for Uvicorn Import Failures
# ─────────────────────────────────────────────────────────────
import sys
import os

print(f"📂 Current working directory: {os.getcwd()}")
print(f"📦 sys.path before patch: {sys.path}")

app_dir = os.path.dirname(__file__)
if app_dir not in sys.path:
    sys.path.append(app_dir)

print(f"📦 sys.path after patch: {sys.path}")

# ─────────────────────────────────────────────────────────────
# ✅ Core Imports
# ─────────────────────────────────────────────────────────────
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
import logging
import json
from datetime import datetime

from orchestration.utils.redis import get_redis_client

# ─────────────────────────────────────────────────────────────
# ✅ Route Imports (from orchestration)
# ─────────────────────────────────────────────────────────────
try:
    from orchestration.routes.config import router as config_router
    from orchestration.routes.exports import router as exports_router
    from orchestration.routes.tolerances import router as tolerances_router
    from orchestration.routes.violations import router as violations_router
    from orchestration.routes.labels import router as labels_router
    from orchestration.routes.license import router as license_router
    from orchestration.routes.history import router as history_router

    print("✅ Route imports successful")
except Exception as e:
    print(f"❌ Route import failed: {e}")
    raise

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
    r = get_redis_client()
    r.ping()
    app.state.redis = r
    logging.info("✅ Connected to Redis")
except Exception as e:
    logging.error(f"❌ Redis connection failed: {e}")
    app.state.redis = None

# ─────────────────────────────────────────────────────────────
# ✅ Route Registration
# ─────────────────────────────────────────────────────────────
try:
    app.include_router(config_router)
    app.include_router(exports_router)
    app.include_router(tolerances_router, prefix="/v1/model")
    app.include_router(violations_router, prefix="/v1/model/violations")
    app.include_router(labels_router, prefix="/v1/labels")
    app.include_router(license_router, prefix="/v1/license")
    app.include_router(history_router, prefix="/v1/history")
    logging.info("✅ All routers registered")
except Exception as e:
    logging.error(f"❌ Router registration failed: {e}")
    raise

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
# ✅ GET /health → Full Infra Check
# ─────────────────────────────────────────────────────────────
@app.get("/health")
def health_check_full():
    try:
        r = get_redis_client()
        r.ping()
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestration", "model_config.json"))
        with open(config_path) as f:
            config = json.load(f)
        return {"status": "ok", "models": [m["model_id"] for m in config.get("models", [])]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

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
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestration", "model_config.json"))

    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"[MMS-API] ❌ Failed to read {config_path}: {e}")
        return {"error": "Configuration file not found or invalid"}

    model = next((m for m in config.get("models", []) if m["model_id"] == model_id), None)
    if not model:
        return {"error": "Model not found"}

    export_dir = model.get("export_path")
    filepath = os.path.join(export_dir, filename)

    if not os.path.exists(filepath):
        logging.warning(f"[MMS-API] ❌ File not found: {filepath}")
        return {"error": "File not found"}

    return FileResponse(path=filepath, filename=filename, media_type="application/json")
