# PET_HEALTH/scripts/streaming_detect.py

import asyncio
import struct
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
import pickle

import numpy as np
from bleak import BleakScanner, BleakClient
import pytz

TEMP_UUID   = "2A6E"
HUM_UUID    = "2A6F"
IMU_UUID    = "A001"
DEVICE_NAME = "NanoSense"

# Decode functions
def decode_temp(data):
    return struct.unpack("<h", data)[0] / 100.0

def decode_humidity(data):
    return struct.unpack("<H", data)[0] / 100.0

def decode_imu(data):
    return struct.unpack("<fff", data)

async def main():
    # 1) Load scaler, model, and threshold
    project_root = Path(__file__).resolve().parent.parent
    scaler_path  = project_root / "model" / "scaler.pkl"
    model_path   = project_root / "model" / "iso_multivar.pkl"
    thresh_path  = project_root / "data" / "threshold.pkl"

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(model_path, "rb") as f:
        iso = pickle.load(f)
    with open(thresh_path, "rb") as f:
        threshold = pickle.load(f)

    # 2) Prepare to write live_data.csv
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_path = data_dir / "live_data.csv"
    f = open(out_path, mode="w", newline="")
    writer = csv.writer(f)
    # Write header with raw + accel_mag + anomaly_flag
    header = [
        "timestamp", "temp_C", "humidity_%", "accel_x", "accel_y", "accel_z",
        "accel_mag", "anomaly"
    ]
    writer.writerow(header)
    f.flush()

    # 3) Scan and connect to BLE device
    print("Press ENTER to start live anomaly detection…")
    await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

    print("Scanning for device...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    if not device:
        print("Device not found. Exiting.")
        f.close()
        return

    async with BleakClient(device) as client:
        await asyncio.sleep(2)
        print("Connected. Starting live anomaly detection. Press ENTER again to stop.")

        # Schedule a task to wait for ENTER to stop
        stop_event = asyncio.Event()

        async def wait_for_enter():
            await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            stop_event.set()

        asyncio.create_task(wait_for_enter())

        # 4) Loop: read BLE once per second until ENTER is pressed
        while not stop_event.is_set():
            try:
                raw_t   = await client.read_gatt_char(TEMP_UUID)
                raw_h   = await client.read_gatt_char(HUM_UUID)
                raw_imu = await client.read_gatt_char(IMU_UUID)

                t = decode_temp(raw_t)
                h = decode_humidity(raw_h)
                x, y, z = decode_imu(raw_imu)

                # Timestamp in US/Eastern
                est = pytz.timezone("US/Eastern")
                now = datetime.now(est).isoformat()

                # Compute accel magnitude
                accel_mag = np.sqrt(x**2 + y**2 + z**2)

                # Scale and score
                feats = np.array([[t, h, x, y, z, accel_mag]])
                X_scaled = scaler.transform(feats)
                score = iso.decision_function(X_scaled)[0]  # higher = more normal
                anomaly = 1 if score < threshold else 0   # 1=anomaly, 0=normal

                # Print immediately if anomaly
                if anomaly == 1:
                    print(f"[{now}]  ANOMALY DETECTED  (score={score:.3f} < {threshold:.3f})")

                # Write one row: timestamp, raw features, accel_mag, anomaly flag
                writer.writerow([now, t, h, x, y, z, accel_mag, anomaly])
                f.flush()

                await asyncio.sleep(1)
            except Exception as e:
                print("Error during BLE read:", e)
                break

    f.close()
    print(f"Live session ended. Data saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
