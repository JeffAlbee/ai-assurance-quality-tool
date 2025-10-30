from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
import time

router = APIRouter()
LOG_FILE = "assurance_labels.log"

@router.post("/")
async def receive_label(request: Request):
    try:
        payload = await request.json()
        payload["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(payload) + "\n")
        return JSONResponse(content={"status": "label logged"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
