
//Use the following command to build and upload the firmware:
// pio run
// pio run --target upload
// Use the following command to monitor the serial output:
// pio device monitor

#include <ArduinoBLE.h>
#include <Arduino_HS300x.h>
#include <Arduino_BMI270_BMM150.h>


// BLE Service and Characteristics
BLEService sensorService("181A");  // Environmental Sensing Service

BLECharacteristic tempCharacteristic("2A6E", BLERead | BLENotify, 2);
BLECharacteristic humCharacteristic ("2A6F", BLERead | BLENotify, 2);
BLECharacteristic imuCharacteristic ("A001", BLERead | BLENotify, 12);

unsigned long lastUpdate = 0;
const unsigned long updateInterval = 1000;

// ── Forward declaration ───────────────────────────────────────────────────────────
void sendSensorData();

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("Initializing sensors...");

  if (!HS300x.begin()) {
    Serial.println("Failed to initialize HS300x!");
    while (1);
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize BMI270 IMU!");
    while (1);
  }

  Serial.println("Sensors initialized.");

  if (!BLE.begin()) {
    Serial.println("Failed to start BLE!");
    while (1);
  }

  BLE.setLocalName("NanoSense");
  BLE.setAdvertisedService(sensorService);

  sensorService.addCharacteristic(tempCharacteristic);
  sensorService.addCharacteristic(humCharacteristic);
  sensorService.addCharacteristic(imuCharacteristic);
  BLE.addService(sensorService);

  BLE.advertise();
  Serial.println("BLE advertising started...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (millis() - lastUpdate >= updateInterval) {
        lastUpdate = millis();
        sendSensorData();
      }
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

// ── Now the definition matches the forward declaration ─────────────────────────────
void sendSensorData() {
  float temperature = HS300x.readTemperature();
  float humidity    = HS300x.readHumidity();
  int16_t tempFixed = (int16_t)(temperature * 100);
  int16_t humFixed  = (int16_t)(humidity * 100);

  tempCharacteristic.writeValue((uint8_t*)&tempFixed, 2);
  humCharacteristic.writeValue((uint8_t*)&humFixed, 2);

  Serial.print("Temperature: "); Serial.print(temperature); Serial.println(" °C");
  Serial.print("Humidity: ");    Serial.print(humidity);    Serial.println(" %");

  float x, y, z;
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);
    uint8_t accelBuffer[12];
    memcpy(&accelBuffer[0], &x, 4);
    memcpy(&accelBuffer[4], &y, 4);
    memcpy(&accelBuffer[8], &z, 4);
    imuCharacteristic.writeValue(accelBuffer, 12);

    Serial.print("Accel X: "); Serial.print(x, 2);
    Serial.print(" Y: ");        Serial.print(y, 2);
    Serial.print(" Z: ");        Serial.println(z, 2);
  }
}

