from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import json

from utils.redis import get_redis_client
from utils.export import export_model_history

router = APIRouter()

# 📁 List export files from disk
@router.get("/v1/exports")
def list_exports(model_id: str):
    try:
        with open("model_config.json") as f:
            config = json.load(f)
        model = next((m for m in config["models"] if m["model_id"] == model_id), None)
        if not model:
            return {"error": "Model not found"}

        export_dir = model["export_path"]
        files = [f for f in os.listdir(export_dir) if f.startswith(model_id)]
        return {"files": sorted(files)}
    except Exception as e:
        print(f"❌ Failed to list exports: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 📦 Return live metric history from Redis with timestamps
@router.get("/v1/exports/raw")
def export_raw_metrics(model_id: str):
    try:
        r = get_redis_client()
        if not r:
            return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

        keys = r.keys(f"metrics:{model_id}:*")
        keys.sort()

        prefix = f"metrics:{model_id}:"
        history = []
        for key in keys:
            if not key.startswith(prefix):
                continue
            raw = r.get(key)
            if raw:
                try:
                    timestamp = key[len(prefix):]  # ✅ Extract everything after the prefix
                    entry = json.loads(raw)
                    history.append({
                        "timestamp": timestamp,
                        **entry
                    })
                except Exception as e:
                    print(f"❌ Failed to parse {key}: {e}")

        print(f"📦 Exported {len(history)} entries for {model_id}")
        return JSONResponse(content=history)

    except Exception as e:
        print(f"❌ Export route crashed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 📁 Optional: Trigger file-based export to disk
@router.get("/v1/exports/file")
def export_to_file(model_id: str):
    try:
        with open("model_config.json") as f:
            config = json.load(f)
        model = next((m for m in config["models"] if m["model_id"] == model_id), None)
        if not model:
            return {"error": "Model not found"}

        export_dir = model["export_path"]
        filepath = export_model_history(model_id, export_dir)
        return {"status": "success", "file": filepath}
    except Exception as e:
        print(f"❌ File export failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
