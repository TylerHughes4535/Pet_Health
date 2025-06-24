#include <ArduinoBLE.h>
#include <Arduino_HS300x.h>
#include <Arduino_BMI270_BMM150.h>
#include <Wire.h>

// TMP-117 I2C address (default)
#define TMP117_ADDRESS    0x48
#define TMP117_TEMP_REG   0x00

// BLE Service and Characteristics
BLEService sensorService("181A");  // Environmental Sensing Service

BLECharacteristic tempCharacteristic("2A6E", BLERead | BLENotify, 2);
BLECharacteristic humCharacteristic("2A6F", BLERead | BLENotify, 2);
BLECharacteristic imuCharacteristic("A001", BLERead | BLENotify, 12);
BLECharacteristic externalTempCharacteristic("A002", BLERead | BLENotify, 2);

// LED indicator pin
const int ledPin = LED_BUILTIN;

unsigned long lastUpdate = 0;
const unsigned long updateInterval = 1000;

// Function prototypes
void scanI2CDevices();
void checkAddress(uint8_t addr);
float readTMP117Temperature();
void sendSensorData();

void setup() {
  // Initialize Serial (non-blocking)
  Serial.begin(9600);

  // LED setup for advertising indicator
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  Serial.println("Initializing sensors...");

  // I2C setup for TMP117
  Wire.begin();
  Wire.setClock(100000);
  pinMode(A4, INPUT_PULLUP); // SDA
  pinMode(A5, INPUT_PULLUP); // SCL

  Serial.println("Scanning for I2C devices...");
  scanI2CDevices();

  Serial.println("Checking TMP117 address...");
  checkAddress(TMP117_ADDRESS);
  Serial.println();

  // On-board HS300x (humidity & ambient temp)
  if (!HS300x.begin()) {
    Serial.println("Failed to initialize HS300x!");
    while (1);
  }

  // On-board IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize BMI270 IMU!");
    while (1);
  }

  Serial.println("Sensors initialized.");

  // Start BLE
  if (!BLE.begin()) {
    Serial.println("Failed to start BLE!");
    while (1);
  }

  BLE.setLocalName("NanoSense");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(tempCharacteristic);
  sensorService.addCharacteristic(humCharacteristic);
  sensorService.addCharacteristic(imuCharacteristic);
  sensorService.addCharacteristic(externalTempCharacteristic);
  BLE.addService(sensorService);

  BLE.advertise();
  Serial.println("BLE advertising started...");

  // Keep LED on to indicate advertising
  digitalWrite(ledPin, HIGH);
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
      BLE.poll();
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  } else {
    BLE.poll();
  }
}

void sendSensorData() {
  // HS300x readings
  float ambientTemp = HS300x.readTemperature();
  float humidity    = HS300x.readHumidity();

  // TMP117 external temperature
  float extTemp      = readTMP117Temperature();

  int16_t ambFixed   = int16_t(ambientTemp * 100);
  int16_t humFixed   = int16_t(humidity * 100);
  int16_t extFixed   = isnan(extTemp) ? 0 : int16_t(extTemp * 100);

  tempCharacteristic.writeValue((uint8_t*)&ambFixed, 2);
  humCharacteristic.writeValue((uint8_t*)&humFixed, 2);
  externalTempCharacteristic.writeValue((uint8_t*)&extFixed, 2);

  Serial.print("Ambient Temp: "); Serial.print(ambientTemp, 2); Serial.println(" °C");
  Serial.print("Humidity: ");     Serial.print(humidity, 2);      Serial.println(" %");
  if (!isnan(extTemp)) {
    Serial.print("External Temp: "); Serial.print(extTemp, 2); Serial.println(" °C");
  } else {
    Serial.println("External Temp: ERR");
  }

  // IMU readings
  float x, y, z;
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);
    uint8_t accelBuffer[12];
    memcpy(accelBuffer, &x, 4);
    memcpy(accelBuffer + 4, &y, 4);
    memcpy(accelBuffer + 8, &z, 4);
    imuCharacteristic.writeValue(accelBuffer, 12);

    Serial.print("Accel X: "); Serial.print(x, 2);
    Serial.print(" Y: ");      Serial.print(y, 2);
    Serial.print(" Z: ");      Serial.println(z, 2);
  }
}

void scanI2CDevices() {
  uint8_t error, address;
  int deviceCount = 0;
  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at 0x");
      if (address < 16) Serial.print('0');
      Serial.println(address, HEX);
      deviceCount++;
    }
  }
  if (deviceCount == 0) {
    Serial.println("No I2C devices found! Check wiring.");
  } else {
    Serial.print("Total I2C devices: "); Serial.println(deviceCount);
  }
}

void checkAddress(uint8_t addr) {
  Wire.beginTransmission(addr);
  if (Wire.endTransmission() == 0) {
    Serial.print("TMP117 found at 0x"); Serial.println(addr, HEX);
  } else {
    Serial.print("TMP117 NOT found at 0x"); Serial.println(addr, HEX);
  }
}

float readTMP117Temperature() {
  Wire.beginTransmission(TMP117_ADDRESS);
  Wire.write(TMP117_TEMP_REG);
  if (Wire.endTransmission() != 0) return NAN;
  Wire.requestFrom(TMP117_ADDRESS, (uint8_t)2);
  if (Wire.available() < 2) return NAN;
  uint16_t raw = (Wire.read() << 8) | Wire.read();
  return (int16_t)raw * 0.0078125;
}
