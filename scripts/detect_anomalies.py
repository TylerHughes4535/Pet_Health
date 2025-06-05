# PET_HEALTH/scripts/detect_anomalies.py

import os
import pandas as pd
import numpy as np
import pickle

# -------------- CONFIGURATION --------------
# Any feature with |z| > Z_THRESHOLD is considered a direct contributor.
Z_THRESHOLD = 3.0

# -------------- HELPERS --------------
def load_and_convert(path):
    """
    Load CSV from 'path' (which may have a naive or tz-aware 'timestamp'),
    ensure 'timestamp' is tz-aware US/Eastern, and add a 12-hour 'time_str'.
    """
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    df["timestamp"] = df["timestamp"].dt.tz_convert("US/Eastern")
    df["time_str"] = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# -------------- LOAD BASELINE STATS --------------
# We need baseline means + stddevs to compute per-feature z-scores.
base_dir      = os.path.dirname(os.path.dirname(__file__))
baseline_path = os.path.join(base_dir, "data", "baseline.csv")
baseline_df   = load_and_convert(baseline_path)

# List of raw features (exactly as you collected them)
feature_list = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"]
baseline_stats = {}
for f in feature_list:
    mu    = baseline_df[f].mean()
    sigma = baseline_df[f].std(ddof=0)
    baseline_stats[f] = {"mean": mu, "std": sigma}

# -------------- LOAD TRAINED ARTIFACTS --------------
scaler_path   = os.path.join(base_dir, "model", "scaler.pkl")
model_path    = os.path.join(base_dir, "model", "iso_multivar.pkl")
threshold_path= os.path.join(base_dir, "data", "threshold.pkl")

with open(scaler_path,   "rb") as f: scaler = pickle.load(f)
with open(model_path,    "rb") as f: iso    = pickle.load(f)
with open(threshold_path,"rb") as f: threshold = pickle.load(f)

# -------------- PROMPT & LOAD UNLABELED CSV --------------
print("Enter the filename (in data/) you want to label (e.g. 'live_data.csv'):")
filename   = input().strip()
input_path = os.path.join(base_dir, "data", filename)

if not os.path.exists(input_path):
    print(f"Error: File not found → {input_path}")
    exit(1)

df = load_and_convert(input_path)

# -------------- FEATURE ENGINEERING ON NEW DATA --------------
# Compute the same accel magnitude used during training
df["accel_mag"] = np.sqrt(
    df["accel_x"]**2 + df["accel_y"]**2 + df["accel_z"]**2
)

# Build the array of features in the exact order used in training
features_for_model = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z", "accel_mag"]
X = df[features_for_model].values

# -------------- SCALE & SCORE --------------
X_scaled = scaler.transform(X)
scores   = iso.decision_function(X_scaled)       # higher = more normal
df["anomaly_score"] = scores
df["raw_anomaly"]   = np.where(scores < threshold, -1, 1)
df["label_overall"] = df["raw_anomaly"].map({1: "normal", -1: "anomaly"})

# -------------- COMPUTE PER-FEATURE Z-SCORES --------------
for f in feature_list:
    mu    = baseline_stats[f]["mean"]
    sigma = baseline_stats[f]["std"]
    if sigma == 0:
        df[f"z_{f}"] = 0.0
    else:
        df[f"z_{f}"] = (df[f] - mu) / sigma

# -------------- DETERMINE CONTRIBUTING FEATURES --------------
def find_contributors(row):
    # First, gather any features whose absolute z-score > Z_THRESHOLD
    flagged = []
    for f in feature_list:
        if abs(row[f"z_{f}"]) > Z_THRESHOLD:
            flagged.append(f)
    # If no single feature crossed the threshold, but the overall label is "anomaly",
    # set flagged to ["multivariate"] so we always indicate a cause.
    if (not flagged) and (row["label_overall"] == "anomaly"):
        flagged = ["multivariate"]
    return ",".join(flagged)

df["contributing_features"] = df.apply(find_contributors, axis=1)

# -------------- SAVE LABELED OUTPUT --------------
results_dir = os.path.join(base_dir, "data", "results")
os.makedirs(results_dir, exist_ok=True)
output_path = os.path.join(results_dir, "new_data_labeled.csv")
df.to_csv(output_path, index=False)

print(f"\nBatch‐labeling complete → {output_path}")
