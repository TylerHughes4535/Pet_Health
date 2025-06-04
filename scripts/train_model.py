import os
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest

# Helper: load baseline, parse dates, and ensure US/Eastern
def load_baseline(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # If timestamp is naive (no tz), localize → UTC, else skip localization
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    # Convert any tz (UTC or already tz-aware) to US/Eastern
    df["timestamp"] = df["timestamp"].dt.tz_convert("US/Eastern")
    # Optional: keep a human-readable 12-hour string
    df["time_str"] = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# Path to baseline.csv (one level up from scripts/)
baseline_path = os.path.join("..", "data", "baseline.csv")

# 1. Load baseline
baseline_df = load_baseline(baseline_path)

# 2. Feature list
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"]

# 3. Train one IsolationForest per feature
models = {}
for feat in features:
    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(baseline_df[[feat]])
    models[feat] = iso

# 4. Ensure model/ folder exists
os.makedirs(os.path.join("..", "model"), exist_ok=True)

# 5. Pickle the dict of models
out_path = os.path.join("..", "model", "anomaly_models.pkl")
with open(out_path, "wb") as f:
    pickle.dump(models, f)

print(f"Training complete → saved models to {out_path}")
