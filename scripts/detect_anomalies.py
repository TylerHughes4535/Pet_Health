# PET_HEALTH/scripts/detect_anomalies.py

import os
import pandas as pd
import numpy as np
import pickle

# Helper: load and ensure timestamp is US/Eastern
def load_and_convert(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    df["timestamp"] = df["timestamp"].dt.tz_convert("US/Eastern")
    df["time_str"] = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# 1) Load scaler, model, threshold
base_dir   = os.path.dirname(os.path.dirname(__file__))
scaler_p   = os.path.join(base_dir, "model", "scaler.pkl")
model_p    = os.path.join(base_dir, "model", "iso_multivar.pkl")
thresh_p   = os.path.join(base_dir, "data", "threshold.pkl")

with open(scaler_p, "rb") as f:
    scaler = pickle.load(f)
with open(model_p, "rb") as f:
    iso = pickle.load(f)
with open(thresh_p, "rb") as f:
    threshold = pickle.load(f)

# 2) Ask user for which CSV to label
print("Enter the relative path under data/ to the CSV you want to detect (e.g. 'live_data.csv'):")
filename = input().strip()
input_path = os.path.join(base_dir, "data", filename)
if not os.path.exists(input_path):
    print(f"File not found: {input_path}")
    exit(1)

# 3) Load the CSV
df = load_and_convert(input_path)

# 4) Compute accel magnitude
df["accel_mag"] = np.sqrt(
    df["accel_x"]**2 +
    df["accel_y"]**2 +
    df["accel_z"]**2
)

# 5) Select features and scale
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z", "accel_mag"]
X = df[features].values
X_scaled = scaler.transform(X)

# 6) Compute anomaly scores and labels
scores = iso.decision_function(X_scaled)
df["anomaly_score"] = scores
df["raw_anomaly"] = np.where(scores < threshold, -1, 1)
df["label"] = df["raw_anomaly"].map({1: "normal", -1: "anomaly"})

# 7) Save to data/results/new_data_labeled.csv
out_dir = os.path.join(base_dir, "data", "results")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "new_data_labeled.csv")
df.to_csv(out_path, index=False)

print(f"Anomaly labeling complete → {out_path}")
