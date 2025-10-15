from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import time
import os

app = FastAPI()
LOG_FILE = "assurance_labels.log"

@app.post("/v1/labels")
async def receive_label(request: Request):
    try:
        label = await request.json()
        label["received_at"] = time.time()

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(label) + "\n")

        return JSONResponse(content={"status": "ok", "message": "Label logged"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
