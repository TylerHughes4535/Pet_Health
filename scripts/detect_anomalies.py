import os
import pandas as pd
import pickle

# 1. Load the pickled model dict
model_path = os.path.join("..", "model", "anomaly_model.pkl")
with open(model_path, "rb") as f:
    models = pickle.load(f)
# "models" is a dict: { "temp_C": IsolationForest(...), "humidity_%": ..., ... }

# 2. Load the new (unlabeled) data
new_data_path = os.path.join("..", "data", "new_data.csv")
df = pd.read_csv(new_data_path, parse_dates=["timestamp"])

# 3. If you need timezone conversion as in baseline, do it here:
df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
df["time_str"]  = df["timestamp"].dt.strftime("%I:%M:%S %p")

# 4. For each feature, run predict(…) and store both raw and string labels
features = ["temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"]
for feat in features:
    iso = models[feat]
    raw_pred = iso.predict(df[[feat]])               # array of {1, -1}
    df[f"raw_anomaly_{feat}"] = raw_pred
    df[f"label_{feat}"] = pd.Series(raw_pred).map({1: "normal", -1: "anomaly"})

# 5. Create a summary column listing all features flagged as anomaly in that row
def collect_anomalies(row):
    flagged = [feat for feat in features if row[f"label_{feat}"] == "anomaly"]
    return ",".join(flagged)

df["anomaly_features"] = df.apply(collect_anomalies, axis=1)

# 6. Ensure the results folder exists, then save
out_dir = os.path.join("..", "data", "results")
os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, "new_data_labeled.csv")
df.to_csv(out_path, index=False)

print(f"Anomaly detection complete → labeled file saved to {out_path}")
