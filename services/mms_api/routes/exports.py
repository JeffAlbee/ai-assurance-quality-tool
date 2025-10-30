import os
import json
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from mms_api.utils.redis import get_redis_client
from mms_api.utils.export import export_model_history

router = APIRouter()
logger = logging.getLogger("exports")
logging.basicConfig(level=logging.INFO)

# 📁 List export files from disk
@router.get("/v1/exports")
def list_exports(model_id: str):
    try:
        with open("model_config.json") as f:
            config = json.load(f)
        model = next((m for m in config.get("models", []) if m.get("model_id") == model_id), None)
        if not model:
            return JSONResponse(status_code=404, content={"error": "Model not found"})

        export_dir = model.get("export_path")
        if not os.path.exists(export_dir):
            return JSONResponse(status_code=404, content={"error": "Export directory not found"})

        files = [f for f in os.listdir(export_dir) if f.startswith(model_id)]
        logger.info(f"📁 Found {len(files)} export files for model {model_id}")
        return {"files": sorted(files)}

    except Exception as e:
        logger.error(f"❌ Failed to list exports for {model_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 📦 Return live metric history from Redis with timestamps
@router.get("/v1/exports/raw")
def export_raw_metrics(model_id: str):
    try:
        r = get_redis_client()
        if not r:
            return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

        keys = sorted(r.keys(f"metrics:{model_id}:*"))
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
        return JSONResponse(content=history)

    except Exception as e:
        logger.error(f"❌ Export raw metrics failed for {model_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 📁 Trigger file-based export to disk
@router.get("/v1/exports/file")
def export_to_file(model_id: str):
    try:
        with open("model_config.json") as f:
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
