#include <Arduino.h>
#include <LovyanGFX.hpp>
#include <Wire.h>
#include <Adafruit_AHTX0.h>
#include "bitmaps.h" 
#include "config.h" 

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
Adafruit_AHTX0 ahtFront;
Adafruit_AHTX0 ahtRear;

// --- Custom Colors ---
#define tftViolet lcd.color565(148, 0, 211)
#define tftDarkGrey lcd.color565(80, 80, 80)

// --- State Machine Variables ---
unsigned long lastPayloadTime = 0;
bool isOnline = false;
bool forceRedraw = true; 

// --- System Variables ---
String inputString = "";
bool stringComplete = false;

float caseTemp = 0.0;
float caseHum = 0.0;
bool frontInit = false;
bool rearInit = false;
unsigned long lastSensorRead = 0;
String activeSensorLabel = "AMB:";

int lastDiskState = -1;
int lastPwrState = -1;

// --- Color Helpers ---
uint16_t getTempColor(int temp) {
  if (temp < 50) return TFT_GREEN;
  else if (temp < 65) return TFT_YELLOW;
  else if (temp < 80) return TFT_ORANGE;
  else if (temp < 90) return TFT_RED;
  else return tftViolet;
}

uint16_t getLoadColor(int load) {
  if (load < 40) return TFT_GREEN;
  else if (load < 65) return TFT_YELLOW;
  else if (load < 85) return TFT_ORANGE;
  else if (load < 95) return TFT_RED;
  else return tftViolet;
}

uint16_t getFanColor(int rpm) {
  if (rpm < 1000) return TFT_GREEN;
  else if (rpm < 1500) return TFT_YELLOW;
  else if (rpm < 2000) return TFT_ORANGE;
  else if (rpm < 2500) return TFT_RED;
  else return tftViolet;
}

// --- Layout Generator ---
void drawBaseLayout() {
  lcd.fillScreen(TFT_BLACK);
  int divY = isLandscape ? 125 : 240;
  int width = isLandscape ? 320 : 172;
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
  Serial.begin(serialBaudRate);
  pinMode(hddLedPin, INPUT_PULLUP);
  pinMode(pwrLedPin, INPUT_PULLUP);
  
  // 1. Route hardware bus to Front Sensor pins & initialize
  Wire.begin(i2c0SdaPin, i2c0SclPin);
  if (ahtFront.begin(&Wire)) frontInit = true;

  // 2. Route hardware bus to Rear Sensor pins & initialize
  Wire.begin(i2c1SdaPin, i2c1SclPin);
  if (ahtRear.begin(&Wire)) rearInit = true;

  lcd.init();
  if (isLandscape) lcd.setRotation(1);
  else lcd.setRotation(2);

  lcd.setBrightness(bootBrightness); 
  isOnline = false;
  forceRedraw = true;
}

void loop() {
  unsigned long currentMillis = millis();

  pinMode(hddLedPin, INPUT_PULLUP);
  pinMode(pwrLedPin, INPUT_PULLUP);

  int diskState = (analogRead(hddLedPin) < ledThreshold) ? LOW : HIGH;
  int pwrState = (analogRead(pwrLedPin) < ledThreshold) ? LOW : HIGH;

  if (diskState != lastDiskState) {
    uint16_t hddColor = (diskState == LOW) ? TFT_GREEN : tftDarkGrey;
    int hddX = isLandscape ? 240 : 140; 
    int hddY = isLandscape ? 132 : 245;
    lcd.drawBitmap(hddX, hddY, epd_bitmap_hdd, 32, 32, hddColor, (uint16_t)TFT_BLACK);
    lastDiskState = diskState;
  }

  if (pwrState != lastPwrState) {
    uint16_t pwrColor = (pwrState == LOW) ? TFT_GREEN : tftDarkGrey;
    int pwrX = isLandscape ? 280 : 140; 
    int pwrY = isLandscape ? 132 : 282;
    lcd.drawBitmap(pwrX, pwrY, epd_bitmap_pwr, 32, 32, pwrColor, (uint16_t)TFT_BLACK);
    lastPwrState = pwrState;
  }

  // =================================================================
  // I2C BUS HOPPING LOGIC
  // =================================================================
  if ((frontInit || rearInit) && (currentMillis - lastSensorRead >= sensorPollMs)) {
    float tempF = -999.0, humF = 0.0;
    float tempR = -999.0, humR = 0.0;
    
    // Hop bus to Front Sensor
    if (frontInit) {
      Wire.begin(i2c0SdaPin, i2c0SclPin); 
      sensors_event_t humidity, temp;
      ahtFront.getEvent(&humidity, &temp);
      tempF = temp.temperature;
      humF = humidity.relative_humidity;
    }
    
    // Hop bus to Rear Sensor
    if (rearInit) {
      Wire.begin(i2c1SdaPin, i2c1SclPin);
      sensors_event_t humidity, temp;
      ahtRear.getEvent(&humidity, &temp);
      tempR = temp.temperature;
      humR = humidity.relative_humidity;
    }
    
    // Logic: Identify and store the maximum temperature value
    if (tempF >= tempR && tempF != -999.0) {
      caseTemp = tempF;
      caseHum = humF;
      activeSensorLabel = "AMB F:";
    } else if (rearInit && tempR != -999.0) {
      caseTemp = tempR;
      caseHum = humR;
      activeSensorLabel = "AMB R:";
    }

    lastSensorRead = currentMillis;

    int divY = isLandscape ? 125 : 240;
    lcd.setTextSize(2);
    lcd.setTextColor(TFT_GREEN, TFT_BLACK);

    if (isLandscape) {
      lcd.setCursor(10, divY + 15); lcd.print(activeSensorLabel);
      lcd.setCursor(95, divY + 15); lcd.printf("%02d C  ", (int)caseTemp);
      lcd.setCursor(160, divY + 15); lcd.print("HUM:");
      lcd.setCursor(215, divY + 15); lcd.printf("%02d%%  ", (int)caseHum);
    } else {
      lcd.setCursor(5, divY + 15); lcd.print(activeSensorLabel);
      lcd.setCursor(80, divY + 15); lcd.printf("%02d C  ", (int)caseTemp);
      lcd.setCursor(5, divY + 45); lcd.print("HUM:");
      lcd.setCursor(80, divY + 45); lcd.printf("%02d%%  ", (int)caseHum);
    }
  }

  // =================================================================
  // SERIAL & DISPLAY LOGIC 
  // =================================================================
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '<') { inputString = "<"; }
    else if (inChar != '\n' && inChar != '\r') { inputString += inChar; }
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
        lastPayloadTime = currentMillis; 
        
        if (!isOnline) {
          isOnline = true;
          forceRedraw = true; 
        }

        if (b != -1) lcd.setBrightness(b);

        if (forceRedraw) {
          drawBaseLayout();
          forceRedraw = false;
        }

        // --- SHIFTED Y-COORDINATES ---
        lcd.setTextSize(2);
        if (isLandscape) {
          int col1_L = 10, col1_V = 96, col2_L = 170, col2_V = 256;
          
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.setCursor(col1_L, 25); lcd.print("CPU:");
          lcd.setCursor(col1_V, 25); lcd.printf("%02d C  ", t);

          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.setCursor(col2_L, 25); lcd.print("GPU:");
          lcd.setCursor(col2_V, 25); lcd.printf("%02d C  ", g_t);

          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.setCursor(col1_L, 60); lcd.print("FAN:");
          lcd.setCursor(col1_V, 60); lcd.printf("%04d  ", r);

          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.setCursor(col2_L, 60); lcd.print("SSD:");
          lcd.setCursor(col2_V, 60); lcd.printf("%02d C  ", m);

          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.setCursor(col1_L, 95); lcd.print("CPU L:");
          lcd.setCursor(col1_V, 95); lcd.printf("%02d%%  ", c_l);

          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.setCursor(col2_L, 95); lcd.print("GPU L:");
          lcd.setCursor(col2_V, 95); lcd.printf("%02d%%  ", g_l);
        } else {
          int col_L = 10, col_V = 96;

          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.setCursor(col_L, 30); lcd.print("CPU:");
          lcd.setCursor(col_V, 30); lcd.printf("%02d C  ", t);

          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.setCursor(col_L, 65); lcd.print("GPU:");
          lcd.setCursor(col_V, 65); lcd.printf("%02d C  ", g_t);

          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.setCursor(col_L, 100); lcd.print("FAN:");
          lcd.setCursor(col_V, 100); lcd.printf("%04d  ", r);

          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.setCursor(col_L, 135); lcd.print("SSD:");
          lcd.setCursor(col_V, 135); lcd.printf("%02d C  ", m);

          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.setCursor(col_L, 170); lcd.print("CPU L:");
          lcd.setCursor(col_V, 170); lcd.printf("%02d%%  ", c_l);

          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.setCursor(col_L, 205); lcd.print("GPU L:");
          lcd.setCursor(col_V, 205); lcd.printf("%02d%%  ", g_l);
        }
      }
    }
    inputString = "";
    stringComplete = false;
  }

  if (isOnline && (currentMillis - lastPayloadTime > offlineTimeoutMs)) {
    isOnline = false;
    forceRedraw = true; 
    lcd.setBrightness(standbyBrightness); 
  }

  if (!isOnline && forceRedraw) {
    drawBaseLayout();
    
    lcd.setTextColor(TFT_GREEN, TFT_BLACK);
    lcd.setTextSize(2);
    // Shifted Standby text to clear hotspot
    lcd.setCursor(10, 30);
    lcd.print("SYS NOMINAL");
    
    lcd.setCursor(10, 55);
    lcd.setTextSize(1);
    lcd.print("> Awaiting Daemon...");

    if (isLandscape) lcd.drawBitmap(96, 0, epd_bitmap_pipboy, 128, 128, TFT_GREEN);
    else lcd.drawBitmap(22, 85, epd_bitmap_pipboy, 128, 128, TFT_GREEN);
    
    forceRedraw = false;
  }
}