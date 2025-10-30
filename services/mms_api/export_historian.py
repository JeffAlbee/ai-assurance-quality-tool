import redis, json, os
from datetime import datetime

def export_model_history(model_id, export_dir):
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    keys = sorted(r.keys(f"metrics:{model_id}:*"))

    filename = f"{model_id}_history_{datetime.utcnow().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(export_dir, filename)

    with open(filepath, "w") as f:
        for key in keys:
            entry = r.get(key)
            f.write(json.dumps({key: json.loads(entry)}, indent=2) + "\n")

if __name__ == "__main__":
    with open("model_config.json") as f:
        config = json.load(f)

    for model in config["models"]:
        export_model_history(model["model_id"], model["export_path"])
