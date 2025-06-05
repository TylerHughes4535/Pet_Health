# PET_HEALTH/scripts/train_model.py

import os
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Helper: load baseline, parse dates, ensure US/Eastern
def load_baseline(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # If timestamp is naive, localize → UTC; else skip localization
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    # Convert to US/Eastern
    df["timestamp"] = df["timestamp"].dt.tz_convert("US/Eastern")
    # Keep a human-readable time string if desired
    df["time_str"] = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# 1) Path to data/baseline.csv (one level up from scripts/)
baseline_path = os.path.join("..", "data", "baseline.csv")
baseline_df = load_baseline(baseline_path)

# 2) Feature engineering on baseline
#    a) Compute accel magnitude
baseline_df["accel_mag"] = np.sqrt(
    baseline_df["accel_x"]**2 +
    baseline_df["accel_y"]**2 +
    baseline_df["accel_z"]**2
)

#    b) (Optional) More features, e.g. rolling stats. Can be added here.

# 3) Select features for training
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z", "accel_mag"]
X_baseline = baseline_df[features].values

# 4) Scale features
scaler = StandardScaler().fit(X_baseline)
X_scaled = scaler.transform(X_baseline)

# 5) Train a multivariate IsolationForest
iso = IsolationForest(contamination=0.05, random_state=42)
iso.fit(X_scaled)

# 6) Choose a threshold from baseline anomaly scores (e.g. 5th percentile)
scores_baseline = iso.decision_function(X_scaled)  # higher = more normal
threshold = np.percentile(scores_baseline, 5)      # bottom 5% → anomaly

# 7) Save scaler, model, and threshold
os.makedirs(os.path.join("..", "model"), exist_ok=True)
with open(os.path.join("..", "model", "scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)
with open(os.path.join("..", "model", "iso_multivar.pkl"), "wb") as f:
    pickle.dump(iso, f)
os.makedirs(os.path.join("..", "data"), exist_ok=True)
with open(os.path.join("..", "data", "threshold.pkl"), "wb") as f:
    pickle.dump(threshold, f)

print("Training complete:")
print(" → model/scaler.pkl")
print(" → model/iso_multivar.pkl")
print(" → data/threshold.pkl")
