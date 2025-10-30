from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
import os

router = APIRouter()

CONFIG_PATH = "model_config.json"

@router.post("/v1/model/config")
async def save_model_config(request: Request):
    data = await request.json()

    required_fields = ["model_id", "endpoint", "export_path"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return JSONResponse(status_code=400, content={"error": f"Missing fields: {', '.join(missing)}"})

    # Load or initialize config file
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({"models": []}, f)

    with open(CONFIG_PATH, "r+") as f:
        config = json.load(f)
        config["models"] = [m for m in config["models"] if m["model_id"] != data["model_id"]]
        config["models"].append(data)
        f.seek(0)
        json.dump(config, f, indent=2)
        f.truncate()

    return {
        "status": "saved",
        "model_id": data["model_id"],
        "endpoint": data["endpoint"],
        "export_path": data["export_path"]
    }
