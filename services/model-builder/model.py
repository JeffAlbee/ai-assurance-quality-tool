import random

def predict(input_features):
    label = "safe" if sum(input_features.values()) % 2 == 0 else "unsafe"
    confidence = round(random.uniform(0.8, 0.95), 2)
    return {
        "label": label,
        "confidence": confidence
    }
