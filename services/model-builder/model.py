import random

class FloodRiskModel:
    def predict(self, features_batch):
        """
        Predict flood risk category based on rainfall thresholds.
        features_batch: list of [rainfall_mm, bridge_type_encoded]
        """
        results = []
        for input_features in features_batch:
            rainfall = input_features[0]

            # Threshold logic
            if rainfall < 70:
                label = "flood_risk_low"
            elif rainfall < 140:
                label = "flood_risk_medium"
            else:
                label = "flood_risk_high"

            # Confidence stub
            confidence = round(random.uniform(0.8, 0.95), 2)

            results.append({
                "label": label,
                "confidence": confidence
            })
        return results

def load_model(model_id: str):
    print(f"🔧 Loading model for {model_id}")
    return FloodRiskModel()

# ✅ Top-level predict function for FastAPI import
model_instance = load_model("flood-risk-predictor")

def predict(inputs):
    return model_instance.predict(inputs)
