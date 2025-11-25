import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from orchestration.utils.redis import get_redis_client

router = APIRouter()
logger = logging.getLogger("exports")
logging.basicConfig(level=logging.INFO)

# Make config path container-safe
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model_config.json"))

# ─────────────────────────────────────────────────────────────
# 📦 Core Export Logic (Redis → JSON file)
# ─────────────────────────────────────────────────────────────
def export_model_history(model_id: str, export_dir: str) -> str:
    r = get_redis_client()
    if not r:
        raise ConnectionError("Redis unavailable")

    keys = sorted(r.keys(f"metrics:{model_id}:*") or [])
    if not keys:
        raise ValueError(f"No metrics found for model_id: {model_id}")

    filename = f"{model_id}_history_{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(export_dir, filename)
    os.makedirs(export_dir, exist_ok=True)

    with open(filepath, "w") as f:
        for key in keys:
            raw = r.get(key)
            if raw:
                try:
                    entry = json.loads(raw)
                    f.write(json.dumps({key: entry}, indent=2) + "\n")
                except Exception as e:
                    logger.warning(f"❌ Failed to parse {key}: {e}")

    logger.info(f"✅ Exported {len(keys)} entries to {filepath}")
    return filepath

# ─────────────────────────────────────────────────────────────
# 📁 List export files from disk
# ─────────────────────────────────────────────────────────────
@router.get("/v1/exports")
def list_exports(model_id: str):
    try:
        logger.info(f"📁 Listing exports for model_id: {model_id}")
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        model = next((m for m in config.get("models", []) if m.get("model_id") == model_id), None)
        if not model:
            return JSONResponse(status_code=404, content={"error": "Model not found"})

        export_dir = model.get("export_path")
        if not os.path.exists(export_dir):
            logger.warning(f"📂 Export directory not found: {export_dir}")
            return JSONResponse(status_code=404, content={"error": "Export directory not found"})

        files = [f for f in os.listdir(export_dir) if f.startswith(model_id)]
        logger.info(f"📁 Found {len(files)} export files for model {model_id}")
        return {"files": sorted(files)}

    except Exception as e:
        logger.error(f"❌ Failed to list exports for {model_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ─────────────────────────────────────────────────────────────
# 📦 Return live metric history from Redis with timestamps
# ─────────────────────────────────────────────────────────────
@router.get("/v1/exports/raw")
def export_raw_metrics(model_id: str):
    try:
        logger.info(f"📦 Exporting raw metrics for model_id: {model_id}")
        r = get_redis_client()
        if not r:
            logger.error("❌ Redis unavailable")
            return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

        keys = sorted(r.keys(f"metrics:{model_id}:*") or [])
        prefix = f"metrics:{model_id}:"
        history = []

        for key in keys:
            if not key.startswith(prefix):
                continue
            raw = r.get(key)
            if raw:
                try:
                    timestamp = key[len(prefix):]
                    entry = json.loads(raw)
                    history.append({
                        "timestamp": timestamp,
                        **entry
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse Redis entry {key}: {e}")

        logger.info(f"📦 Exported {len(history)} entries for {model_id}")
        return {"model_id": model_id, "entries": history}

    except Exception as e:
        logger.error(f"❌ Export raw metrics failed for {model_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ─────────────────────────────────────────────────────────────
# 📁 Trigger file-based export to disk
# ─────────────────────────────────────────────────────────────
@router.get("/v1/exports/file")
def export_to_file(model_id: str):
    try:
        logger.info(f"📁 Triggering file export for model_id: {model_id}")
        with open(CONFIG_PATH) as f:
            config = json.load(f)

        model = next((m for m in config.get("models", []) if m.get("model_id") == model_id), None)
        if not model:
            return JSONResponse(status_code=404, content={"error": "Model not found"})

        export_dir = model.get("export_path")
        filepath = export_model_history(model_id, export_dir)
        logger.info(f"📁 Exported file for {model_id} → {filepath}")
        return {"status": "success", "file": filepath}

    except Exception as e:
        logger.error(f"❌ File export failed for {model_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# ─────────────────────────────────────────────────────────────
# 🩺 Health check for export service
# ─────────────────────────────────────────────────────────────
@router.get("/v1/exports/health")
def export_health_check():
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return {"status": "ok", "models": [m["model_id"] for m in config.get("models", [])]}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
