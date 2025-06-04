# PET_HEALTH/scripts/collect_ble_data.py

import asyncio
import struct
import csv
import sys
from datetime import datetime
from pathlib import Path

from bleak import BleakScanner, BleakClient
import pytz

# UUIDs for your BLE characteristics
TEMP_UUID = "2A6E"
HUM_UUID  = "2A6F"
IMU_UUID  = "A001"
DEVICE_NAME = "NanoSense"

def decode_temp(data):
    return struct.unpack("<h", data)[0] / 100.0

def decode_humidity(data):
    return struct.unpack("<H", data)[0] / 100.0

def decode_imu(data):
    return struct.unpack("<fff", data)

async def main(outfile_name):
    # 1. Determine project root and data/ folder
    #    This assumes this script lives in PET_HEALTH/scripts/
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 2. Full path to the CSV inside data/
    out_path = data_dir / outfile_name

    # 3. Scan for the BLE device by name
    print("Scanning for device...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    if not device:
        print("Device not found.")
        return

    # 4. Connect and start reading
    async with BleakClient(device) as client:
        # small delay to ensure connection is fully established
        await asyncio.sleep(2)
        print("Connected. Starting read loop...")

        # 5. Open the CSV in write mode under data/
        with open(out_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            # Write header row
            writer.writerow(["timestamp", "temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"])

            while True:
                try:
                    # 6. Read each characteristic
                    raw_t = await client.read_gatt_char(TEMP_UUID)
                    raw_h = await client.read_gatt_char(HUM_UUID)
                    raw_imu = await client.read_gatt_char(IMU_UUID)

                    t = decode_temp(raw_t)
                    h = decode_humidity(raw_h)
                    x, y, z = decode_imu(raw_imu)

                    # 7. Timestamp in US/Eastern
                    est = pytz.timezone("US/Eastern")
                    now = datetime.now(est).isoformat()

                    # 8. Write one row
                    writer.writerow([now, t, h, x, y, z])
                    f.flush()  # ensure it’s written to disk immediately

                    # 9. Print to console
                    print(f"{now}  Temp: {t:.2f}  Humidity: {h:.2f}  IMU: {x:.2f}, {y:.2f}, {z:.2f}")

                    await asyncio.sleep(1)  # wait 1 second before next read
                except Exception as e:
                    print("Error during BLE read:", e)
                    break

    print(f"Finished. Data saved to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python collect_ble_data.py <output_filename.csv>")
    else:
        asyncio.run(main(sys.argv[1]))

