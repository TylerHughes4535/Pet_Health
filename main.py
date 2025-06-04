from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

# Load CSVs
baseline_df = pd.read_csv("baseline.csv")
anomaly_df = pd.read_csv("anomaly.csv")

# Parse and format timestamps
baseline_df["timestamp"] = pd.to_datetime(baseline_df["timestamp"]).dt.tz_localize("UTC").dt.tz_convert("US/Eastern")
anomaly_df["timestamp"] = pd.to_datetime(anomaly_df["timestamp"]).dt.tz_localize("UTC").dt.tz_convert("US/Eastern")

baseline_df["timestamp"] = baseline_df["timestamp"].dt.strftime("%I:%M:%S %p")
anomaly_df["timestamp"] = anomaly_df["timestamp"].dt.strftime("%I:%M:%S %p")

# Combine data
combined_df = pd.concat([baseline_df, anomaly_df], ignore_index=True)

# Use relevant features
features = ["temperature", "humidity", "accel_x", "accel_y", "accel_z"]
X = combined_df[features]

# Train Isolation Forest only on baseline
clf = IsolationForest(contamination=0.1, random_state=42)
clf.fit(baseline_df[features])

# Predict anomalies
combined_df["anomaly"] = clf.predict(X)
combined_df["anomaly_label"] = combined_df["anomaly"].map({1: "normal", -1: "anomaly"})

# Plot
plt.figure(figsize=(12, 6))
plt.plot(combined_df["timestamp"], combined_df["temperature"], label="Temperature")
plt.scatter(
    combined_df["timestamp"][combined_df["anomaly"] == -1],
    combined_df["temperature"][combined_df["anomaly"] == -1],
    color="red", label="Anomaly", zorder=5
)
plt.xticks(rotation=45)
plt.xlabel("Time (EST)")
plt.ylabel("Temperature (°C)")
plt.title("Anomaly Detection in Temperature")
plt.legend()
plt.tight_layout()
plt.show()

# Save to CSV
combined_df.to_csv("combined_results.csv", index=False)

    
    

    
