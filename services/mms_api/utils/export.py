import json
import os
from datetime import datetime
from utils.redis import get_redis_client

def export_model_history(model_id: str, export_dir: str) -> str:
    r = get_redis_client()
    if not r:
        raise ConnectionError("Redis unavailable")

    keys = sorted(r.keys(f"metrics:{model_id}:*"))
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
                    print(f"❌ Failed to parse {key}: {e}")

    print(f"✅ Exported {len(keys)} entries to {filepath}")
    return filepath
