import asyncio, struct, csv, sys
from datetime import datetime
from bleak import BleakScanner, BleakClient
import pytz

TEMP_UUID = "2A6E"
HUM_UUID = "2A6F"
IMU_UUID = "A001"
DEVICE_NAME = "NanoSense"

def decode_temp(data): return struct.unpack("<h", data)[0] / 100.0
def decode_humidity(data): return struct.unpack("<H", data)[0] / 100.0
def decode_imu(data): return struct.unpack("<fff", data)

est = pytz.timezone("US/Eastern")
timestamp = datetime.now(est).strftime("%I:%M:%S %p")


async def main(outfile):
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    if not device:
        print("Device not found.")
        return

    async with BleakClient(device) as client:
        await asyncio.sleep(2)
        print("Connected. Starting read loop...")

        with open(outfile, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "temp_C", "humidity_%", "accel_x", "accel_y", "accel_z"])

            while True:
                try:
                    t = decode_temp(await client.read_gatt_char(TEMP_UUID))
                    h = decode_humidity(await client.read_gatt_char(HUM_UUID))
                    x, y, z = decode_imu(await client.read_gatt_char(IMU_UUID))
                    now = datetime.now().isoformat()
                    writer.writerow([now, t, h, x, y, z])
                    print(f"{now}  Temp: {t:.2f}  Humidity: {h:.2f}  IMU: {x:.2f}, {y:.2f}, {z:.2f}")
                    await asyncio.sleep(1)
                except Exception as e:
                    print("Error:", e)
                    break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python collect_ble_data.py <output.csv>")
    else:
        asyncio.run(main(sys.argv[1]))

    
    
