# PET_HEALTH/scripts/run_pipeline.py

import subprocess
import time
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
# Duration settings (in seconds). Adjust as needed:
BASELINE_DURATION   = 10   # e.g. 600 s = 10 minutes for baseline collection
NEWDATA_DURATION    = 10   # 10 minutes for new/test data collection
WAIT_BEFORE_NEWDATA = 10   # 60 s pause between baseline training and new data

# Filenames (stored under data/)
BASELINE_FILENAME = "baseline.csv"
NEWDATA_FILENAME  = "new_data.csv"
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Locate project structure
    project_root = Path(__file__).resolve().parent.parent
    scripts_dir  = project_root / "scripts"

    print("\n=== STEP 1: Collecting baseline data ===")
    subprocess.run([
        "python",
        str(scripts_dir / "collect_ble_data.py"),
        BASELINE_FILENAME,
        str(BASELINE_DURATION)
    ], check=True)

    print("\n=== STEP 2: Training IsolationForest models on baseline ===")
    subprocess.run([
        "python",
        str(scripts_dir / "train_model.py")
    ], check=True)

    print(f"\nWaiting {WAIT_BEFORE_NEWDATA} seconds before collecting new data...\n")
    time.sleep(WAIT_BEFORE_NEWDATA)

    print("=== STEP 3: Collecting new/test data ===")
    subprocess.run([
        "python",
        str(scripts_dir / "collect_ble_data.py"),
        NEWDATA_FILENAME,
        str(NEWDATA_DURATION)
    ], check=True)

    print("\n=== STEP 4: Detecting anomalies in new data ===")
    subprocess.run([
        "python",
        str(scripts_dir / "detect_anomalies.py")
    ], check=True)

    print("\n=== Pipeline complete! ===")
    print("→ Baseline CSV:   data/" + BASELINE_FILENAME)
    print("→ Model pickle:   model/anomaly_models.pkl")
    print("→ New data CSV:   data/" + NEWDATA_FILENAME)
    print("→ Labeled output: data/results/new_data_labeled.csv\n")
