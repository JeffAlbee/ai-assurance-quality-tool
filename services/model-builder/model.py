import random

class DummyModel:
    def predict(self, features_batch):
        results = []
        for input_features in features_batch:
            label = "safe" if sum(input_features) % 2 == 0 else "unsafe"
            confidence = round(random.uniform(0.8, 0.95), 2)
            results.append({
                "label": label,
                "confidence": confidence
            })
        return results

def load_model(model_id: str):
    print(f"🔧 Loading model for {model_id}")
    return DummyModel()

# ✅ Top-level predict function for FastAPI import
model_instance = load_model("flood-risk-predictor")

def predict(inputs):
    return model_instance.predict(inputs)
