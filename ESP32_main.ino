// GPS Positioning through the NEO-7M GPS module. Communication via bluetooth, with JSON structure.
// This is a code for the ESP3 STEAMakers. It's meant to work with the Geofencing Application by Leo Sarria
#include <Wire.h>
#include <TinyGPSPlus.h>
#include <LiquidCrystal_I2C.h>
#include "BluetoothSerial.h"

// Hardware config
static const uint8_t GPS_RX_PIN = 16;   // (D5) RX of the ESP32 <- TX from GPS module
static const uint32_t GPS_BAUD   = 9600;

static const uint8_t LCD_ADDR = 0x27;
static const uint8_t LCD_COLS = 16;
static const uint8_t LCD_ROWS = 2;

HardwareSerial& GPSSerial = Serial2;
TinyGPSPlus gps;
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);
BluetoothSerial SerialBT;

double distancia_total_m   = 0.0;
uint32_t contador_muestras = 0;
double lat_prev = 0.0, lon_prev = 0.0;
const double VEL_MIN_KMH   = 4.0;

uint32_t t_last_ui = 0;
const uint32_t UI_PERIOD_MS = 1500;

static inline bool hasFix()
{
  if (!gps.location.isValid()) return false;
  if (gps.location.age() > 5000) return false;
  return true;
}

// Positioning State
static inline const char* clasificarEstado()
{
  if (!gps.location.isValid() || gps.location.age() > 5000) return "SEARCHING";
  int sats = gps.satellites.isValid() ? gps.satellites.value() : 0;
  double hdop = gps.hdop.isValid() ? gps.hdop.value() / 100.0 : 99.9;
  if (sats > 0 && (sats < 5 || hdop > 2.5)) return "UNSURE";
  return "FIXED";
}

static inline void gpsUpdate()
{
  while (GPSSerial.available())
    gps.encode(GPSSerial.read());
}

static inline double haversine(double lat1, double lon1, double lat2, double lon2)
{
  return TinyGPSPlus::distanceBetween(lat1, lon1, lat2, lon2); // metros
}

static void calcularDistanciaTotal()
{
  double vel = gps.speed.kmph();
  if (vel > VEL_MIN_KMH && gps.location.isValid())
  {
    double lat = gps.location.lat();
    double lon = gps.location.lng();
    if (contador_muestras > 0)
      distancia_total_m += haversine(lat_prev, lon_prev, lat, lon);
    lat_prev = lat;
    lon_prev = lon;
    ++contador_muestras;
  }
}

static void lcdWelcome()
{
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("Arduino ESP32");
  lcd.setCursor(0, 1); lcd.print("GPS listo");
  delay(3000);
}

static void lcdMostrarDatos()
{
  lcd.clear();
  const double vel = gps.speed.kmph();
  const double alt = gps.altitude.meters();
  lcd.setCursor(0, 0);
  char l1[17];
  snprintf(l1, sizeof(l1), "%4.1fkm/h %4dm", vel, (int)alt);
  lcd.print(l1);
  lcd.setCursor(0, 1);
  char l2[17];
  snprintf(l2, sizeof(l2), "Dist: %.2f km", distancia_total_m / 1000.0);
  lcd.print(l2);
}

static void lcdMostrarError()
{
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("Sin datos GPS");
  lcd.setCursor(0, 1); lcd.print("Esperando...");
}

static void consolaMostrarDatos()
{
  const char* estado = clasificarEstado();
  double vel = gps.speed.kmph();
  double alt = gps.altitude.meters();
  double lat = gps.location.isValid() ? gps.location.lat() : 0.0;
  double lon = gps.location.isValid() ? gps.location.lng() : 0.0;
  int    sats = gps.satellites.isValid() ? gps.satellites.value() : -1;
  double hdop = gps.hdop.isValid() ? gps.hdop.value() / 100.0 : -1.0;

  Serial.print(F("Estado: ")); Serial.print(estado);
  Serial.print(F(" | Vel: ")); Serial.print(vel, 2); Serial.print(F(" km/h"));
  Serial.print(F(" | Alt: ")); Serial.print((int)alt); Serial.print(F(" m"));
  Serial.print(F(" | Dist: ")); Serial.print(distancia_total_m / 1000.0, 3); Serial.print(F(" km"));
  Serial.print(F(" | Lat: ")); Serial.print(lat, 6);
  Serial.print(F(" | Lon: ")); Serial.print(lon, 6);
  Serial.print(F(" | Sats: ")); Serial.print(sats);
  Serial.print(F(" | HDOP: ")); Serial.println(hdop, 2);
}

// This sends via bluetooth a JSON message. Or via SERIAL if there's no bluetooth client.
static void btEnviarLineaJSON()
{
  char buf[256];
  const char* estado = clasificarEstado(); // This can send SEARCHING, UNSURE or FIXED
  bool locOK = gps.location.isValid() && gps.location.age() < 10000;
  double lat = locOK ? gps.location.lat() : 0.0;  // IMPORTANT! If there's no position fix, it will send lat= 0, lon= 0
  double lon = locOK ? gps.location.lng() : 0.0;
  double alt = gps.altitude.meters(); // Heigh (in metrs)
  double vel = gps.speed.kmph(); // Velocity (in km/s)
  int sats = gps.satellites.isValid() ? gps.satellites.value() : -1; // Connected satellites
  double hdop = gps.hdop.isValid() ? gps.hdop.value() / 100.0 : -1.0; // hdop
  snprintf(buf, sizeof(buf),
    "{\"ts\":%lu,\"estado\":\"%s\",\"lat\":%.6f,\"lon\":%.6f,\"alt\":%.1f,\"vel_kmh\":%.2f,\"sats\":%d,\"hdop\":%.2f}\n",
    (unsigned long)(millis()/1000UL),
    estado,
    lat,
    lon,
    alt,
    vel,
    sats,
    hdop
  );

  if (SerialBT.hasClient()) {
    SerialBT.print(buf);
  } else {
    // Sends via SERIAL
    Serial.print("[BT-inactivo] ");
    Serial.print(buf);
  }
}



void setup()
{
  Serial.begin(115200);

  GPSSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, -1);

// Bluetooth
  if (!SerialBT.begin("GPS-ESP32")) {
    Serial.println("Error: Bluetooth not initialized");
  } else {
    Serial.println("Bluetooth SPP iniciated: GPS-ESP32");
  }

  // I2C and LCD
  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  lcdWelcome();

  distancia_total_m = 0.0;
  contador_muestras = 0;
  lat_prev = lon_prev = 0.0;
  t_last_ui = millis();
}

void loop()
{
  gpsUpdate();

  if (millis() - t_last_ui >= UI_PERIOD_MS)
  {
    t_last_ui = millis();
    if (hasFix())
    {
      calcularDistanciaTotal();
      lcdMostrarDatos();
    }
    else
    {
      lcdMostrarError();
    }
    consolaMostrarDatos();
    btEnviarLineaJSON();
  }
}
