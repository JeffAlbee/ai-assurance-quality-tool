from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
import json

router = APIRouter()

@router.get("/")
def get_model_history(
    request: Request,
    model_id: str = Query(..., description="Model ID to fetch history for")
):
    redis_conn = request.app.state.redis
    if not redis_conn:
        return JSONResponse(status_code=503, content={"error": "Redis unavailable"})

    pattern = f"metrics:{model_id}:*"
    keys = redis_conn.keys(pattern)

    history = []
    for key in sorted(keys):
        try:
            entry = redis_conn.get(key)
            if entry:
                history.append(json.loads(entry))
        except Exception:
            continue

    return {
        "model_id": model_id,
        "count": len(history),
        "history": history
    }
