import asyncio
import struct
from bleak import BleakScanner, BleakClient

DEVICE_NAME     = "NanoSense"
TEMP_UUID       = "2A6E"
HUM_UUID        = "2A6F"
IMU_UUID        = "A001"  # Custom 12-byte characteristic (3 floats)

def decode_temp_hum(data: bytearray) -> float:
    return struct.unpack("<h", data)[0] / 100.0

def decode_imu(data: bytearray) -> tuple:
    x = struct.unpack('<f', data[0:4])[0]
    y = struct.unpack('<f', data[4:8])[0]
    z = struct.unpack('<f', data[8:12])[0]
    return x, y, z

async def main():
    print("🔍 Scanning for NanoSense...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    if not device:
        print("❌ Device not found.")
        return

    print(f"✅ Found: {device.name} [{device.address}]")
    async with BleakClient(device) as client:
        if not client.is_connected:
            print("❌ Could not connect.")
            return

        print(f"🔗 Connected: {device.address}")
        print("🔄 Discovering services...")
        services = await client.get_services()
        print("✅ Services discovered.")

        while True:
            try:
                temp_data = await client.read_gatt_char(TEMP_UUID)
                hum_data = await client.read_gatt_char(HUM_UUID)
                imu_data = await client.read_gatt_char(IMU_UUID)

                temp = decode_temp_hum(temp_data)
                hum = decode_temp_hum(hum_data)
                x, y, z = decode_imu(imu_data)

                print(f"Temp: {temp:.2f} °C  | Humidity: {hum:.2f} %")
                print(f"Accel X: {x:.2f}  Y: {y:.2f}  Z: {z:.2f}")
                print("-" * 40)

                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"⚠️ Error during read: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
    
    
