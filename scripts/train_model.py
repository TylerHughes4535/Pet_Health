import os
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest

# 1. Helper to load baseline and convert timestamp
def load_baseline(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # Localize from UTC → US/Eastern
    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
    # (Optional) keep a human-readable string if you want
    df["time_str"] = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# 2. Load your baseline CSV
baseline_path = os.path.join("..", "data", "baseline.csv")
baseline_df = load_baseline(baseline_path)

# 3. Define features you want to train on
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"]

# 4. Train one IsolationForest per feature
models = {}
for feat in features:
    iso = IsolationForest(contamination=0.1, random_state=42)
    # We train ONLY on baseline_df[feat]
    iso.fit(baseline_df[[feat]])
    models[feat] = iso

# 5. Make sure the "model/" folder exists
os.makedirs(os.path.join("..", "model"), exist_ok=True)

# 6. Save (pickle) the dict of models to model/anomaly_models.pkl
out_path = os.path.join("..", "model", "anomaly_model.pkl")
with open(out_path, "wb") as f:
    pickle.dump(models, f)

print(f"Training complete → saved 5 IsolationForest models to {out_path}")
