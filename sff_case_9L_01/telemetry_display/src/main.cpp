#include <Arduino.h>
#include <LovyanGFX.hpp>

// --- Hardware Pin Definitions ---
#define HDD_LED_PIN 4 

// --- Display Configuration ---
// Set to true for Landscape, false for Portrait (USB on top)
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
String inputString = "";
bool stringComplete = false;
bool firstPayloadReceived = false;

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
  if (tagIndex == -1)
    return -1;
  int startIndex = tagIndex + tag.length();
  int endIndex = data.indexOf(endChar, startIndex);
  if (endIndex == -1)
    endIndex = data.indexOf('>', startIndex);
  return data.substring(startIndex, endIndex).toInt();
}

void setup()
{
  Serial.begin(115200);
  
  // Initialize Optocoupler Input
  pinMode(HDD_LED_PIN, INPUT);

  lcd.init();
  
  // Apply the orientation based on configuration
  if (IS_LANDSCAPE) {
    lcd.setRotation(1); // Landscape
  } else {
    lcd.setRotation(2); // Portrait, inverted (USB at top)
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
  // 1. Process Hardware Disk IO (Zero Latency via Optocoupler)
  int diskState = digitalRead(HDD_LED_PIN);
  
  // Adjust indicator position based on orientation
  int dotX = IS_LANDSCAPE ? 300 : 150; 
  
  if (diskState == LOW) {
    lcd.fillCircle(dotX, 10, 5, TFT_GREEN); // Active
  } else {
    lcd.fillCircle(dotX, 10, 5, TFT_BLACK); // Idle
  }

  // 2. Serial Ingestion
  while (Serial.available())
  {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>')
      stringComplete = true;
  }

  // 3. Payload Parsing
  if (stringComplete)
  {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0)
    {
      // Extract values
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
          firstPayloadReceived = true;
        }

        lcd.setTextSize(2);

        if (IS_LANDSCAPE) 
        {
          // ROW 1: Temps 
          lcd.setCursor(10, 20);
          lcd.setTextColor(getTempColor(t), TFT_BLACK);
          lcd.printf("CPU: %02d C  ", t);
          
          lcd.setCursor(170, 20);
          lcd.setTextColor(getTempColor(g_t), TFT_BLACK);
          lcd.printf("GPU: %02d C  ", g_t);

          // ROW 2: Dynamics (Fan & SSD)
          lcd.setCursor(10, 60);
          lcd.setTextColor(getFanColor(r), TFT_BLACK);
          lcd.printf("FAN: %04d  ", r);
          
          lcd.setCursor(170, 60);
          lcd.setTextColor(getTempColor(m), TFT_BLACK);
          lcd.printf("SSD: %02d C  ", m);

          // ROW 3: System Load
          lcd.setCursor(10, 100);
          lcd.setTextColor(getLoadColor(c_l), TFT_BLACK);
          lcd.printf("CPU L: %02d%%  ", c_l);
          
          lcd.setCursor(170, 100);
          lcd.setTextColor(getLoadColor(g_l), TFT_BLACK);
          lcd.printf("GPU L: %02d%%  ", g_l);
        } 
        else 
        {
          // Portrait Layout
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