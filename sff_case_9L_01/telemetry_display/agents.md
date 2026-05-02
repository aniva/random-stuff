# Project: 9L SFF PC Build & Migration
**Author:** Aniva
**Date:** May 2, 2026

## 1. Project Overview & Strategic Objectives
Migration of hardware from an A01 Aluminum Mini-ITX chassis to a custom ~9L SFF enclosure. 
* **Commercial Productization:** Engineer and market a distinct, proprietary SFF chassis design (CAD files and fabricated units). 
* **Visual Optimization (120Hz):** Achieve native 4K @ 120Hz output for an 85" Samsung display.
* **Hardware Acceleration:** Maximize Insta360 Studio timeline scrubbing and export encoding performance.
* **Hardware Telemetry Integration:** Deploy a microcontroller-driven front panel display for real-time thermal monitoring.

## 2. Custom Fabrication Details
* **Chassis Material (Re-Printed):** Polymaker PC-PBT. Scrapped ABS to permanently eliminate toxic styrene off-gassing (VOCs) under ambient internal temperatures exceeding 50°C. 
* **Assembly Architecture:** Modular panels secured via M3 bolts. Captive nut recesses calibrated to 5.65mm - 5.70mm in Shapr3D.
* **Dimensional Divergence:** Height increased for top exhaust fans; Width +1mm for routing; Length +10mm (Max GPU limit: ~252mm).
* **Power Delivery:** Custom internal extension. IEC C14 inlet wiring standard utilized: Green (Top/Ground), Black (Right/Line), White (Left/Neutral). Custom 90-degree IEC C13 plug interfaces with the PSU.

## 3. Hardware Specifications (Active Build)
| Component | Specification |
| :--- | :--- |
| **Motherboard** | ASRock B760M-ITX/D4 WiFi (UEFI Version 11.02) |
| **Processor** | Intel Core i3-12100 (Pending Migration to i5-14400) |
| **CPU Cooler** | Noctua NH-L9i-17xx Premium Low-Profile (Brown) |
| **Memory** | 32GB (2x16GB) DDR4 @ 3200 MHz (XMP Profile Active) |
| **Storage** | 512GB Samsung PM991 NVMe M.2 / 2x 1TB Crucial MX500 SATA SSD |
| **GPU** | NVIDIA GeForce GTX 1650 SUPER (ASUS ROG STRIX 4G) |
| **GPU Riser** | LINKUP AVA5 PCIE 5.0 Double Reverse (21cm total length) |
| **Power Supply** | FSP Dagger Pro 850W SFX 3.1 |
| **Telemetry Display** | Waveshare ESP32-C6 1.47inch Touch Display (172×320, v0.2 Hardware Revision) |

### 3.1. Hardware Acceleration Pipeline (Insta360 Studio)
* **Primary Graphics Adapter (UEFI):** `[PCIE1]`. Forces 120Hz display output and NVENC hardware encoding via the discrete NVIDIA GPU.
* **IGPU Multi-Monitor (UEFI):** `[Enabled]`. Exposes Intel Quick Sync Video (QSV) silicon to the OS for efficient background HEVC/H.265 timeline decoding without overriding the discrete GPU.

## 4. Pending Actions
* [ ] **Physical CPU Migration:** Execute swap to Intel Core i5-14400. Strict adjustment of PL1/PL2 power limits required in UEFI to prevent thermal throttling against the Noctua NH-L9i-17xx.
* [ ] **Front Panel Fabrication:** Measure exact physical tolerances of the Waveshare ESP32-C6 PCB and Type-C port using digital calipers. Execute Shapr3D cuts for flush mount.
* [ ] **GPU Upgrade Execution:** Procure a sub-252mm NVIDIA GPU optimized for Insta360 Studio and native 120Hz display output via HDMI 2.1 (~$300 CAD secondary market). Options: RTX 4060 8GB or RTX 3060 12GB.

## 5. Telemetry & Hardware Monitoring Architecture
* **Microcontroller:** Waveshare ESP32-C6 Development Board. Pinout mapped for hardware revision v0.2 (Backlight: GPIO 22, Data/Command: GPIO 15).
* **Firmware Stack:** C++ compiled via PlatformIO. Utilizes `LovyanGFX` for hardware-native ST7789 display driving with a 34px X-axis offset memory correction. 

### 5.1. Host Infrastructure & Deployment
* **Hardware Monitoring Engine:** LibreHardwareMonitor (LHM). 
    * Must be executed as Administrator.
    * WMI Server must be explicitly enabled via `Options -> Run WMI Server` to broadcast kernel-level thermals to the OS.
* **Python Environment:** Global Windows Python 3.14 installation required. Executed via the `py` launcher. Dependencies: `pip install wmi pyserial`.
* **Host Daemon:** Python script (`telemetry_stream.py`) querying the LHM WMI namespace. Extracts CPU Temp/Fan RPM and transmits formatted binary strings (`<T:XX,R:XXXX>`) to the ESP32-C6 over the virtual USB CDC COM port every 2.0s.
* **Startup Initialization:** VBScript wrapper (`launch_telemetry.vbs`) configured in Windows `shell:startup` to execute the Python daemon silently (`pythonw.exe`) in the background on user login.

## 6. ESP32-C6 Display Recovery & Initialization Protocol
Required execution path when the module is stuck in a Watchdog Timer (WDT) boot-loop, presents a blank LCD panel, or drops the native USB serial connection.

### 6.1. Flash Memory Erase
Delete the hidden `.pio` directory to clear corrupted compilation caches. Execute the following in PowerShell to format the chip.

'''powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase
'''

### 6.2. Hardware Interrupt (Download Mode)
If the microcontroller is actively crashing (erratic backlight flashing/strobe), software flashing will fail. The WDT boot-loop must be physically interrupted:
1. Press and hold the physical **BOOT** button on the rear of the module.
2. Short-press the physical **RST** button.
3. Release the **BOOT** button.
The device is now suspended in ROM Download Mode and is receptive to new firmware.

### 6.3. PlatformIO Hardware Configuration (`platformio.ini`)
The v0.2 hardware revision requires `dio` flash mode to prevent crashing, and explicit DTR/RTS assertion to wake up the internal USB CDC interface.

'''ini
[env:esp32-c6-devkitc-1]
platform = espressif32
board = esp32-c6-devkitc-1
framework = arduino
monitor_speed = 115200

; Force safe flash mode to prevent hardware boot-loops
board_build.flash_mode = dio

; Wake up the Native USB CDC stream
monitor_dtr = 1
monitor_rts = 1

build_flags = 
    -D ARDUINO_USB_MODE=1
    -D ARDUINO_USB_CDC_ON_BOOT=1

lib_deps = 
    lovyan03/LovyanGFX@^1.1.16
'''

### 6.4. Hardware Validation Firmware (`src/main.cpp`)
Deploy this minimalist graphical test to verify SPI pin mappings and PWM backlight control prior to integrating serial payload ingestion.

'''cpp
#include <Arduino.h>
#include <LovyanGFX.hpp>

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
      cfg.pin_dc = 15; // Validated v0.2 Data/Command pin
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
      cfg.pin_bl = 22; // Validated v0.2 Hardware Backlight Pin
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
  
  lcd.init();
  lcd.setRotation(1); 
  lcd.setBrightness(128); 
  lcd.fillScreen(TFT_BLACK);
  
  lcd.setTextColor(TFT_GREEN, TFT_BLACK);
  lcd.setTextSize(2);
  lcd.setCursor(10, 10);
  lcd.println("SYSTEM NOMINAL");
  lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  lcd.println("Awaiting Python Daemon...");

  Serial.println("Hardware initialized. SPI Bus active.");
}

void loop() {
  delay(1000);
}
'''

### 6.5. Expected Boot Sequence & Validation
1. **Compilation & Flash:** Terminal reports `[SUCCESS]`.
2. **Execution:** Press the physical **RST** button to boot the new firmware.
3. **USB Mount:** Windows emits the USB connection chime. The ESP32-C6 automatically creates a new Virtual USB Serial COM port.
4. **Visual Output:** The 1.47" LCD activates and displays "SYSTEM NOMINAL" in green text, confirming exact alignment of the SPI and PWM pins.