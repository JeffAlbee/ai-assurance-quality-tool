import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Load data
df = pd.read_csv("training_data.csv")

# Features and target
X = df[["rainfall_mm", "bridge_type_encoded"]]
y = df["target"]

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Save label mapping for inference
label_map = dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))
joblib.dump(label_encoder, "label_encoder.pkl")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Train model
model = LogisticRegression(max_iter=200)
model.fit(X_train, y_train)

# Save model
joblib.dump(model, "FloodRiskModel.pkl")

print("✅ Model trained and saved as FloodRiskModel.pkl")
print("✅ Label encoder saved as label_encoder.pkl")
print("✅ Classes:", label_map)

