#include <Arduino.h>
#include <LovyanGFX.hpp>
#include <Wire.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include "bitmaps.h" // Injects static hex arrays from local header

// --- Hardware Pin Definitions ---
#define HDD_LED_PIN 4 
#define PWR_LED_PIN 5 
#define I2C_SDA_PIN 0
#define I2C_SCL_PIN 1

// --- Custom Colors ---
#define TFT_VIOLET lcd.color565(148, 0, 211)
#define TFT_DARKGREY lcd.color565(80, 80, 80)

// --- Display Configuration ---
const bool IS_LANDSCAPE = false;

// 1. Hardware Configuration Class
class LGFX : public lgfx::LGFX_Device
{
  lgfx::Panel_ST7789 _panel_instance;
  lgfx::Bus_SPI _bus_instance;
  lgfx::Light_PWM _light_instance;

public:
  LGFX(void)
  {
    {
      auto cfg = _bus_instance.config();
      cfg.spi_host = SPI2_HOST;
      cfg.spi_mode = 0;
      cfg.freq_write = 40000000;
      cfg.pin_sclk = 7;
      cfg.pin_mosi = 6;
      cfg.pin_dc = 15;
      _bus_instance.config(cfg);
      _panel_instance.setBus(&_bus_instance);
    }
    {
      auto cfg = _panel_instance.config();
      cfg.pin_cs = 14;
      cfg.pin_rst = 21;
      cfg.panel_width = 172;
      cfg.panel_height = 320;
      cfg.offset_x = 34;
      cfg.invert = true;
      _panel_instance.config(cfg);
    }
    {
      auto cfg = _light_instance.config();
      cfg.pin_bl = 22;
      cfg.freq = 44100;
      _light_instance.config(cfg);
      _panel_instance.setLight(&_light_instance);
    }
    setPanel(&_panel_instance);
  }
};

LGFX lcd;
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;

String inputString = "";
bool stringComplete = false;
bool firstPayloadReceived = false;

float caseTemp = 0.0;
float caseHum = 0.0;
bool sensorsInitialized = false;
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_INTERVAL = 5000;

int lastDiskState = -1;
int lastPwrState = -1;

// --- State Timeout Logic ---
unsigned long lastPayloadTime = 0;
const unsigned long PAYLOAD_TIMEOUT = 10000; 
const int DEFAULT_BRIGHTNESS = 128;
bool signalLost = false;

// --- Color Helpers ---
uint16_t getTempColor(int temp) {
  if (temp < 50) return TFT_GREEN;
  else if (temp < 65) return TFT_YELLOW;
  else if (temp < 80) return TFT_ORANGE;
  else if (temp < 90) return TFT_RED;
  else return TFT_VIOLET;
}

uint16_t getLoadColor(int load) {
  if (load < 40) return TFT_GREEN;
  else if (load < 65) return TFT_YELLOW;
  else if (load < 85) return TFT_ORANGE;
  else if (load < 95) return TFT_RED;
  else return TFT_VIOLET;
}

uint16_t getFanColor(int rpm) {
  if (rpm < 1000) return TFT_GREEN;
  else if (rpm < 1500) return TFT_YELLOW;
  else if (rpm < 2000) return TFT_ORANGE;
  else if (rpm < 2500) return TFT_RED;
  else return TFT_VIOLET;
}

void drawBaseLayout() {
  lcd.fillScreen(TFT_BLACK);
  int divY = IS_LANDSCAPE ? 125 : 240;
  int width = IS_LANDSCAPE ? 320 : 172;
  lcd.drawFastHLine(0, divY, width, TFT_GREEN);
  lastDiskState = -1;
  lastPwrState = -1;
  lastSensorRead = 0; 
}

int getValueByTag(String data, String tag, char endChar) {
  int tagIndex = data.indexOf(tag);
  if (tagIndex == -1) return -1;
  int startIndex = tagIndex + tag.length();
  int endIndex = data.indexOf(endChar, startIndex);
  if (endIndex == -1) endIndex = data.indexOf('>', startIndex);
  return data.substring(startIndex, endIndex).toInt();
}

void setup() {
  Serial.begin(115200);
  pinMode(HDD_LED_PIN, INPUT_PULLUP);
  pinMode(PWR_LED_PIN, INPUT_PULLUP);
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  
  if (aht.begin() && bmp.begin()) {
    sensorsInitialized = true;
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                    Adafruit_BMP280::SAMPLING_X2,
                    Adafruit_BMP280::SAMPLING_X16,
                    Adafruit_BMP280::FILTER_X16,
                    Adafruit_BMP280::STANDBY_MS_500);
  }

  lcd.init();
  if (IS_LANDSCAPE) lcd.setRotation(1); 
  else lcd.setRotation(2); 
  
  lcd.setBrightness(DEFAULT_BRIGHTNESS);
  drawBaseLayout();

  // Draw Initial Top-Section Status
  lcd.setTextColor(TFT_GREEN, TFT_BLACK);
  lcd.setTextSize(2);
  lcd.setCursor(10, 15);
  lcd.print("SYS NOMINAL");
  lcd.setCursor(10, 40);
  lcd.setTextSize(1);
  lcd.print("> Awaiting Daemon...");

  // Draw High-Res 128x128 Vault Boy
  if (IS_LANDSCAPE) {
    lcd.drawBitmap(96, 0, epd_bitmap_pipboy, 128, 128, TFT_GREEN); 
  } else {
    lcd.drawBitmap(22, 85, epd_bitmap_pipboy, 128, 128, TFT_GREEN); 
  }
}

void loop() {
  // Re-assert pull-up logic for hardware indicators
  pinMode(HDD_LED_PIN, INPUT_PULLUP);
  pinMode(PWR_LED_PIN, INPUT_PULLUP);

  int diskState = (analogRead(HDD_LED_PIN) < 3000) ? LOW : HIGH;
  int pwrState  = (analogRead(PWR_LED_PIN) < 3000) ? LOW : HIGH;
  
  if (diskState != lastDiskState) {
    uint16_t hddColor = (diskState == LOW) ? TFT_GREEN : TFT_DARKGREY;
    int hddX = IS_LANDSCAPE ? 240 : 130; 
    int hddY = IS_LANDSCAPE ? 132 : 245;
    lcd.drawBitmap(hddX, hddY, epd_bitmap_hdd, 32, 32, hddColor, (uint16_t)TFT_BLACK);
    lastDiskState = diskState;
  }

  if (pwrState != lastPwrState) {
    uint16_t pwrColor = (pwrState == LOW) ? TFT_GREEN : TFT_DARKGREY;
    int pwrX = IS_LANDSCAPE ? 280 : 130; 
    int pwrY = IS_LANDSCAPE ? 132 : 282; 
    lcd.drawBitmap(pwrX, pwrY, epd_bitmap_pwr, 32, 32, pwrColor, (uint16_t)TFT_BLACK);
    lastPwrState = pwrState;
  }

  // Ambient Polling Section
  if (sensorsInitialized && (millis() - lastSensorRead >= SENSOR_INTERVAL)) {
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);
    caseTemp = temp.temperature;
    caseHum = humidity.relative_humidity;
    lastSensorRead = millis();

    int divY = IS_LANDSCAPE ? 125 : 240;
    lcd.setTextSize(2);
    lcd.setTextColor(TFT_GREEN, TFT_BLACK); 

    if (IS_LANDSCAPE) {
      lcd.setCursor(10, divY + 15);
      lcd.printf("AMB: %02d C", (int)caseTemp);
      lcd.setCursor(120, divY + 15);
      lcd.printf("HUM: %02d%%", (int)caseHum);
    } else {
      lcd.setCursor(10, divY + 15); 
      lcd.printf("AMB: %02d C", (int)caseTemp);
      lcd.setCursor(10, divY + 45); 
      lcd.printf("HUM: %02d%%", (int)caseHum);
    }
  }

  // Fallback Brightness Logic (Host disconnected/Timeout)
  if (firstPayloadReceived && (millis() - lastPayloadTime > PAYLOAD_TIMEOUT)) {
      if (!signalLost) {
          lcd.setBrightness(DEFAULT_BRIGHTNESS);
          signalLost = true;
      }
  }

  // Serial Telemetry Ingestion
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>') stringComplete = true;
  }

  if (stringComplete) {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0) {
      int t = getValueByTag(inputString, "T:", ',');
      int r = getValueByTag(inputString, "R:", ',');
      int g_t = getValueByTag(inputString, "G:", ',');
      int m = getValueByTag(inputString, "M:", ',');
      int c_l = getValueByTag(inputString, "C:", ','); 
      int g_l = getValueByTag(inputString, "L:", ','); 
      int b = getValueByTag(inputString, "B:", '>'); 

      if (t != -1 && r != -1) {
        lastPayloadTime = millis();
        signalLost = false;

        if (b != -1) {
            lcd.setBrightness(b);
        }

        if (!firstPayloadReceived) {
          drawBaseLayout();
          firstPayloadReceived = true;
        }

        lcd.setTextSize(2);
        if (IS_LANDSCAPE) {
          lcd.setCursor(10, 15);
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.printf("CPU: %02d C  ", t);
          lcd.setCursor(170, 15);
          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.printf("GPU: %02d C  ", g_t);
          lcd.setCursor(10, 50);
          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.printf("FAN: %04d  ", r);
          lcd.setCursor(170, 50);
          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.printf("SSD: %02d C  ", m);
          lcd.setCursor(10, 85);
          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.printf("CPU L: %02d%%  ", c_l);
          lcd.setCursor(170, 85);
          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.printf("GPU L: %02d%%  ", g_l);
        } else {
          lcd.setCursor(10, 15);
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.printf("CPU: %02d C  ", t);
          lcd.setCursor(10, 50);
          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.printf("GPU: %02d C  ", g_t);
          lcd.setCursor(10, 85);
          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.printf("FAN: %04d  ", r);
          lcd.setCursor(10, 120);
          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.printf("SSD: %02d C  ", m);
          lcd.setCursor(10, 155);
          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.printf("CPU L: %02d%%  ", c_l);
          lcd.setCursor(10, 190);
          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.printf("GPU L: %02d%%  ", g_l);
        }
      }
    }
    inputString = "";
    stringComplete = false;
  }
}