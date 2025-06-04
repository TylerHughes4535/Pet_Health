import os
import pandas as pd
import pickle

# Helper: load and convert timestamp to US/Eastern if needed
def load_and_convert(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # If timestamp is naive (no tz), localize → UTC
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    # Convert to US/Eastern
    df["timestamp"] = df["timestamp"].dt.tz_convert("US/Eastern")
    df["time_str"]  = df["timestamp"].dt.strftime("%I:%M:%S %p")
    return df

# 1. Load pickled models
model_path = os.path.join("..", "model", "anomaly_models.pkl")
with open(model_path, "rb") as f:
    models = pickle.load(f)  # dict: { feat: IsolationForest(...) }

# 2. Load new_data.csv
new_data_path = os.path.join("..", "data", "new_data.csv")
df = load_and_convert(new_data_path)

# 3. Features to predict on
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"]

# 4. For each feature, predict and label
for feat in features:
    iso = models[feat]
    raw = iso.predict(df[[feat]])                    # array of {1, -1}
    df[f"raw_anomaly_{feat}"] = raw
    df[f"label_{feat}"] = pd.Series(raw).map({1: "normal", -1: "anomaly"})

# 5. Summarize which features are flagged per row
def collect_flags(row):
    flagged = [feat for feat in features if row[f"label_{feat}"] == "anomaly"]
    return ",".join(flagged)

df["anomaly_features"] = df.apply(collect_flags, axis=1)

# 6. Save to data/results/new_data_labeled.csv
out_dir = os.path.join("..", "data", "results")
os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, "new_data_labeled.csv")
df.to_csv(out_path, index=False)

print(f"Anomaly detection complete → output saved to {out_path}")
