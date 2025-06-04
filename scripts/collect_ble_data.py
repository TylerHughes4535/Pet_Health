# PET_HEALTH/scripts/collect_ble_data.py

import asyncio
import struct
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from bleak import BleakScanner, BleakClient
import pytz

TEMP_UUID   = "2A6E"
HUM_UUID    = "2A6F"
IMU_UUID    = "A001"
DEVICE_NAME = "NanoSense"

def decode_temp(data):
    return struct.unpack("<h", data)[0] / 100.0

def decode_humidity(data):
    return struct.unpack("<H", data)[0] / 100.0

def decode_imu(data):
    return struct.unpack("<fff", data)

async def main(outfile_name, duration_sec):
    # 1. Determine project root and data folder
    project_root = Path(__file__).resolve().parent.parent
    data_dir     = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_path     = data_dir / outfile_name

    # 2. Find BLE device
    print("Scanning for device...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    if not device:
        print("Device not found.")
        return

    # 3. Connect and open CSV
    async with BleakClient(device) as client:
        await asyncio.sleep(2)
        print(f"Connected. Recording for {duration_sec} seconds...")

        start_time = time.time()
        with open(out_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"])

            # 4. Loop until duration expires
            while True:
                elapsed = time.time() - start_time
                if elapsed >= duration_sec:
                    print("Duration reached; stopping BLE read.")
                    break

                try:
                    raw_t   = await client.read_gatt_char(TEMP_UUID)
                    raw_h   = await client.read_gatt_char(HUM_UUID)
                    raw_imu = await client.read_gatt_char(IMU_UUID)

                    t = decode_temp(raw_t)
                    h = decode_humidity(raw_h)
                    x, y, z = decode_imu(raw_imu)

                    est = pytz.timezone("US/Eastern")
                    now = datetime.now(est).isoformat()

                    writer.writerow([now, t, h, x, y, z])
                    f.flush()
                    print(f"{now}  Temp: {t:.2f}  Humidity: {h:.2f}  IMU: {x:.2f}, {y:.2f}, {z:.2f}")

                    await asyncio.sleep(1)
                except Exception as e:
                    print("Error during BLE read:", e)
                    break

    print(f"Data saved to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python collect_ble_data.py <output.csv> <duration_seconds>")
    else:
        _, out_name, dur = sys.argv
        asyncio.run(main(out_name, int(dur)))
