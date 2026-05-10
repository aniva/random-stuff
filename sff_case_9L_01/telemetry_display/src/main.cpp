#include <Arduino.h>
#include <LovyanGFX.hpp>
#include <Wire.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>

// --- Hardware Pin Definitions ---
#define HDD_LED_PIN 4 
#define PWR_LED_PIN 5 
#define I2C_SDA_PIN 0
#define I2C_SCL_PIN 1

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

// 2. Global Instances & Variables
LGFX lcd;
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;

String inputString = "";
bool stringComplete = false;
bool firstPayloadReceived = false;

// Sensor Variables & Non-Blocking Timer
float caseTemp = 0.0;
float caseHum = 0.0;
bool sensorsInitialized = false;
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_INTERVAL = 5000;

// Hardware LED State Tracking 
int lastDiskState = -1;
int lastPwrState = -1;

// --- Unified Color Logic Helpers ---
uint16_t getTempColor(int temp) {
  if (temp < 65) return TFT_GREEN;
  else if (temp <= 80) return TFT_ORANGE;
  else return TFT_RED;
}

uint16_t getLoadColor(int load) {
  if (load < 50) return TFT_GREEN;
  else if (load <= 85) return TFT_ORANGE;
  else return TFT_RED;
}

uint16_t getFanColor(int rpm) {
  if (rpm < 1500) return TFT_GREEN;
  else if (rpm <= 2200) return TFT_ORANGE;
  else return TFT_RED;
}

// 3. Helper Function
int getValueByTag(String data, String tag, char endChar)
{
  int tagIndex = data.indexOf(tag);
  if (tagIndex == -1) return -1;
  int startIndex = tagIndex + tag.length();
  int endIndex = data.indexOf(endChar, startIndex);
  if (endIndex == -1) endIndex = data.indexOf('>', startIndex);
  return data.substring(startIndex, endIndex).toInt();
}

void setup()
{
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
  
  if (IS_LANDSCAPE) {
    lcd.setRotation(1); 
  } else {
    lcd.setRotation(2); 
  }
  
  lcd.setBrightness(128);
  lcd.fillScreen(TFT_BLACK);

  lcd.setTextColor(TFT_GREEN, TFT_BLACK);
  lcd.setTextSize(2);
  lcd.setCursor(10, 10);
  lcd.println("SYSTEM NOMINAL");
  lcd.println("Awaiting Daemon...");
}

void loop()
{
  // =================================================================
  // 1. EVENT-DRIVEN HARDWARE LEDs
  // =================================================================
  pinMode(HDD_LED_PIN, INPUT_PULLUP);
  pinMode(PWR_LED_PIN, INPUT_PULLUP);

  int diskState = (analogRead(HDD_LED_PIN) < 3000) ? LOW : HIGH;
  int pwrState  = (analogRead(PWR_LED_PIN) < 3000) ? LOW : HIGH;
  
  if (pwrState != lastPwrState) {
    int pwrDotX = IS_LANDSCAPE ? 280 : 130; 
    if (pwrState == LOW) lcd.fillCircle(pwrDotX, 10, 5, TFT_BLUE); 
    else lcd.fillCircle(pwrDotX, 10, 5, TFT_BLACK); 
    lastPwrState = pwrState;
  }

  if (diskState != lastDiskState) {
    int hddDotX = IS_LANDSCAPE ? 300 : 150; 
    if (diskState == LOW) lcd.fillCircle(hddDotX, 10, 5, TFT_GREEN); 
    else lcd.fillCircle(hddDotX, 10, 5, TFT_BLACK); 
    lastDiskState = diskState;
  }

  // =================================================================
  // 2. NON-BLOCKING LOCAL SENSOR POLLING
  // =================================================================
  if (sensorsInitialized && (millis() - lastSensorRead >= SENSOR_INTERVAL)) {
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);
    caseTemp = temp.temperature;
    caseHum = humidity.relative_humidity;
    lastSensorRead = millis();

    lcd.setTextSize(2);
    lcd.setTextColor(TFT_CYAN, TFT_BLACK);

    if (firstPayloadReceived) {
      if (IS_LANDSCAPE) {
        lcd.setCursor(10, 140);
        lcd.printf("AMB: %02d C  ", (int)caseTemp);
        lcd.setCursor(170, 140);
        lcd.printf("HUM: %02d%%  ", (int)caseHum);
      } else {
        lcd.setCursor(10, 260);
        lcd.printf("AMB: %02d C  ", (int)caseTemp);
        lcd.setCursor(10, 300);
        lcd.printf("HUM: %02d%%  ", (int)caseHum);
      }
    } else {
      if (IS_LANDSCAPE) {
        lcd.setCursor(10, 60); 
      } else {
        lcd.setCursor(10, 80); 
      }
      lcd.printf("Case Amb: %02dC / %02d%%", (int)caseTemp, (int)caseHum);
    }
  }

  // =================================================================
  // 3. SERIAL INGESTION (PC Telemetry)
  // =================================================================
  while (Serial.available())
  {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>') stringComplete = true;
  }

  if (stringComplete)
  {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0)
    {
      int t = getValueByTag(inputString, "T:", ',');
      int r = getValueByTag(inputString, "R:", ',');
      int g_t = getValueByTag(inputString, "G:", ',');
      int m = getValueByTag(inputString, "M:", ',');
      int c_l = getValueByTag(inputString, "C:", ','); 
      int g_l = getValueByTag(inputString, "L:", '>'); 

      if (t != -1 && r != -1)
      {
        if (!firstPayloadReceived)
        {
          lcd.fillScreen(TFT_BLACK);
          lastDiskState = -1;
          lastPwrState = -1;
          firstPayloadReceived = true;
        }

        lcd.setTextSize(2);

        if (IS_LANDSCAPE) 
        {
          lcd.setCursor(10, 20);
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.printf("CPU: %02d C  ", t);
          
          lcd.setCursor(170, 20);
          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.printf("GPU: %02d C  ", g_t);

          lcd.setCursor(10, 60);
          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.printf("FAN: %04d  ", r);
          
          lcd.setCursor(170, 60);
          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.printf("SSD: %02d C  ", m);

          lcd.setCursor(10, 100);
          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.printf("CPU L: %02d%%  ", c_l);
          
          lcd.setCursor(170, 100);
          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.printf("GPU L: %02d%%  ", g_l);
        } 
        else 
        {
          lcd.setCursor(10, 20);
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.printf("CPU: %02d C  ", t);

          lcd.setCursor(10, 60);
          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.printf("GPU: %02d C  ", g_t);

          lcd.setCursor(10, 100);
          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.printf("FAN: %04d  ", r);

          lcd.setCursor(10, 140);
          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.printf("SSD: %02d C  ", m);

          lcd.setCursor(10, 180);
          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.printf("CPU L: %02d%%  ", c_l);

          lcd.setCursor(10, 220);
          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.printf("GPU L: %02d%%  ", g_l);
        }
      }
    }
    inputString = "";
    stringComplete = false;
  }
}