import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

print("[ModelBuilder] 🔍 Loading training data...")
df = pd.read_csv("training_data.csv")

X = df[["rainfall_mm", "bridge_type_encoded"]]
y = df["target"]

print("[ModelBuilder] 🔧 Training flood risk model...")
model = RandomForestClassifier()
model.fit(X, y)

model.version = "FloodRiskModel v1.0 (Python 3.14)"

print("[ModelBuilder] 💾 Saving model to FloodRiskModel.pkl...")
with open("FloodRiskModel.pkl", "wb") as f:
    pickle.dump(model, f)

print("[ModelBuilder] ✅ Model trained and saved.")
