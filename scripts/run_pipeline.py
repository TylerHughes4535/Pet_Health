# PET_HEALTH/scripts/run_pipeline.py

import subprocess
import sys
import time
from pathlib import Path

if __name__ == "__main__":
    # 1) Parse two command‐line arguments: baseline duration and wait time (both in seconds)
    if len(sys.argv) != 3:
        print("Usage: python run_pipeline.py <baseline_seconds> <wait_seconds>")
        sys.exit(1)

    try:
        BASELINE_DURATION   = int(sys.argv[1])
        WAIT_BEFORE_LIVE    = int(sys.argv[2])
    except ValueError:
        print("Both <baseline_seconds> and <wait_seconds> must be integers.")
        sys.exit(1)

    # 2) Define fixed filenames (no user input required)
    BASELINE_FILENAME = "baseline.csv"   # always write baseline to data/baseline.csv
    # live data will always go to data/live_data.csv inside streaming_detect.py

    # 3) Locate project structure
    project_root = Path(__file__).resolve().parent.parent
    scripts_dir  = project_root / "scripts"

    print(f"\n=== STEP 1: Collecting baseline data for {BASELINE_DURATION} seconds ===")
    subprocess.run([
        "python",
        str(scripts_dir / "collect_ble_data.py"),
        BASELINE_FILENAME,
        str(BASELINE_DURATION)
    ], check=True)

    print("Baseline collection complete → data/" + BASELINE_FILENAME)

    print("\n=== STEP 2: Training model on baseline ===")
    subprocess.run([
        "python",
        str(scripts_dir / "train_model.py")
    ], check=True)

    print("Model training complete → model/scaler.pkl, model/iso_multivar.pkl, data/threshold.pkl")

    print(f"\nWaiting {WAIT_BEFORE_LIVE} seconds before starting live anomaly detection…")
    time.sleep(WAIT_BEFORE_LIVE)

    print("\n=== STEP 3: Starting live anomaly detection ===")
    print("Note: streaming_detect.py will write to data/live_data.csv until you press ENTER to stop.\n")
    subprocess.run([
        "python",
        str(scripts_dir / "streaming_detect.py")
    ], check=True)

    print("\n=== Pipeline complete! ===")
    print("  • Baseline CSV:       data/" + BASELINE_FILENAME)
    print("  • Model artifacts:    model/scaler.pkl, model/iso_multivar.pkl")
    print("  • Threshold file:     data/threshold.pkl")
    print("  • Live session CSV:   data/live_data.csv")
    print("You can now load data/live_data.csv into your notebook for analysis.")
