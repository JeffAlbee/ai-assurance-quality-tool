import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dummy-data")

np.random.seed(42)

n_samples = 100
data = {
    "rainfall_mm": np.random.uniform(0, 200, n_samples),
    "bridge_type_encoded": np.random.randint(0, 4, n_samples),
    "target": np.random.choice(["flood_risk_low", "flood_risk_medium", "flood_risk_high"], n_samples)
}

df = pd.DataFrame(data)
df.to_csv("training_data.csv", index=False)

print("[ModelBuilder] ✅ Dummy flood training data generated.")
