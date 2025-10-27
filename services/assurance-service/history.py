from fastapi import APIRouter, Query
import redis
import json

router = APIRouter()

# Connect to Redis
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

@router.get("/v1/history")
def get_model_history(model_id: str = Query(..., description="Model ID to fetch history for")):
    pattern = f"metrics:{model_id}:*"
    keys = r.keys(pattern)

    history = []
    for key in sorted(keys):
        try:
            entry = r.get(key)
            if entry:
                history.append(json.loads(entry))
        except Exception:
            continue

    return {
        "model_id": model_id,
        "count": len(history),
        "history": history
    }
