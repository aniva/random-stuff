#include <Arduino.h>
#include <LovyanGFX.hpp>

// Custom hardware configuration class for Waveshare ESP32-C6 1.47" (v0.2)
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 _panel_instance;
  lgfx::Bus_SPI _bus_instance;
  lgfx::Light_PWM _light_instance;

public:
  LGFX(void) {
    // 1. Configure SPI Bus
    {
      auto cfg = _bus_instance.config();
      cfg.spi_host = SPI2_HOST;
      cfg.spi_mode = 0;
      cfg.freq_write = 40000000;
      cfg.pin_sclk = 7;
      cfg.pin_mosi = 6;
      cfg.pin_miso = -1;
      cfg.pin_dc = 15; // Validated Data/Command pin
      _bus_instance.config(cfg);
      _panel_instance.setBus(&_bus_instance);
    }
    // 2. Configure Panel Parameters
    {
      auto cfg = _panel_instance.config();
      cfg.pin_cs = 14;
      cfg.pin_rst = 21;
      cfg.pin_busy = -1;
      cfg.panel_width = 172;
      cfg.panel_height = 320;
      cfg.offset_x = 34; // Hardware memory offset correction
      cfg.offset_y = 0;
      cfg.invert = true;
      _panel_instance.config(cfg);
    }
    // 3. Configure Hardware Backlight
    {
      auto cfg = _light_instance.config();
      cfg.pin_bl = 22; // Validated Hardware Backlight Pin
      cfg.invert = false;
      cfg.freq = 44100;
      cfg.pwm_channel = 7;
      _light_instance.config(cfg);
      _panel_instance.setLight(&_light_instance);
    }
    setPanel(&_panel_instance);
  }
};

LGFX lcd;

void setup() {
  Serial.begin(115200);
  
  // Initialize graphics pipeline
  lcd.init();
  lcd.setRotation(1); // Set to landscape mode for SFF PC front panel
  lcd.setBrightness(128); // 50% brightness
  lcd.fillScreen(TFT_BLACK);
  
  // Render Test UI
  lcd.setTextColor(TFT_GREEN, TFT_BLACK);
  lcd.setTextSize(2);
  lcd.setCursor(10, 10);
  lcd.println("SYSTEM NOMINAL");
  lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  lcd.println("Awaiting Python Daemon...");

  Serial.println("Hardware initialized. SPI Bus active.");
}

void loop() {
  // Placeholder for serial payload ingestion logic
  delay(1000);
}