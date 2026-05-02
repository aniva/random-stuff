#include <Arduino.h>
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// Hardware Configuration Class
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 _panel_instance;
  lgfx::Bus_SPI      _bus_instance;
  lgfx::Light_PWM    _light_instance;

public:
  LGFX(void) {
    {
      auto cfg = _bus_instance.config();
      cfg.spi_host = SPI2_HOST;  // Native ESP32-C6 SPI
      cfg.freq_write = 40000000;
      cfg.pin_sclk = 7;
      cfg.pin_mosi = 6;
      cfg.pin_miso = -1;
      cfg.pin_dc   = 15;
      _bus_instance.config(cfg);
      _panel_instance.setBus(&_bus_instance);
    }
    {
      auto cfg = _panel_instance.config();
      cfg.pin_cs   = 14;
      cfg.pin_rst  = 21;
      cfg.panel_width  = 172;
      cfg.panel_height = 320;
      cfg.offset_x = 34;  // Injected: Corrects the ST7789 hardware memory shift
      cfg.offset_y = 0;   
      cfg.invert = true; 
      cfg.rgb_order = false;
      _panel_instance.config(cfg);
    }
    {
      auto cfg = _light_instance.config();
      cfg.pin_bl = 22;
      cfg.pwm_channel = 7;
      _light_instance.config(cfg);
      _panel_instance.setLight(&_light_instance);
    }
    setPanel(&_panel_instance);
  }
};

LGFX tft;

// Telemetry State
String inputBuffer = "";
bool newData = false;
int cpuTemp = 0;
int fanRPM = 0;

void setup() {
  Serial.begin(115200);
  
  tft.init();
  tft.setRotation(1); 
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setFont(&fonts::Font4);
  
  // Scaffold UI
  tft.drawString("SFF 9L Telemetry", 10, 10);
  tft.drawLine(10, 35, 310, 35, TFT_DARKGREY);
  tft.drawString("CPU Temp: ", 10, 50);
  tft.drawString("Fan RPM: ", 10, 80);
}

void loop() {
  // Non-blocking serial ingest
  while (Serial.available() > 0 && newData == false) {
    char rc = Serial.read();

    if (rc == '<') {
      inputBuffer = "";
    } 
    else if (rc == '>') {
      newData = true;
    } 
    else {
      inputBuffer += rc;
    }
  }

  // Payload Parsing (<T:XX,R:XXXX>)
  if (newData) {
    int commaIndex = inputBuffer.indexOf(',');
    if (commaIndex > 0) {
      String tempString = inputBuffer.substring(2, commaIndex);
      String rpmString = inputBuffer.substring(commaIndex + 3);
      
      cpuTemp = tempString.toInt();
      fanRPM = rpmString.toInt();

      tft.drawNumber(cpuTemp, 140, 50);
      tft.drawString(" C  ", 180, 50); 
      tft.drawNumber(fanRPM, 140, 80);
      tft.drawString(" RPM", 200, 80);
    }
    newData = false;
  }
}