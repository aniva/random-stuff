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
* [ ] **GPU Upgrade Execution:** Procure a sub-252mm NVIDIA GPU optimized for Insta360 Studio and native 120Hz display output via HDMI 2.1 (~$300 CAD secondary market). Options: RTX 4060 8GB or RTX 3060 12GB.

## 5. Telemetry & Hardware Monitoring Architecture
* **Microcontroller:** Waveshare ESP32-C6 Development Board. Pinout mapped for hardware revision v0.2 (Backlight: GPIO 22, Data/Command: GPIO 15).
* **Firmware Stack:** C++ compiled via PlatformIO. Utilizes `LovyanGFX` for hardware-native ST7789 display driving with a 34px X-axis offset memory correction. 

### 5.1. Host Infrastructure & Deployment
* **Hardware Monitoring Engine:** LibreHardwareMonitor (LHM). 
    * Localhost Web Server explicitly enabled on Port `8085`.
    * HTTP Basic Authentication active (Credentials: `sffmonitor` / `sffmonitor`).
* **Python Environment:** Global Windows Python 3.14 installation required. Executed via the `py` launcher. 
* **Host Daemon:** Python script (`telemetry_stream.py`) querying the LHM JSON namespace. Extracts CPU Temp/Fan RPM and transmits formatted binary strings (`<T:XX,R:XXXX>`) to the ESP32-C6 over the virtual USB CDC COM port every 2.0s. Includes Base64 authentication header construction to bypass LHM security.
* **Startup Initialization:** VBScript wrapper (`launch_telemetry.vbs`) configured in Windows `shell:startup` to execute the Python daemon silently (`pythonw.exe`) in the background on user login.

## 6. ESP32-C6 Display Recovery & Source Code
Required execution paths and source code configurations for the telemetry array.

### 6.1. Flash Memory Erase
If the microcontroller is actively crashing, hold the physical **BOOT** button, short-press **RST**, and release **BOOT** to force Download Mode. Execute the following to wipe the flash memory:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase
```

### 6.2. PlatformIO Configuration (`platformio.ini`)
The v0.2 hardware revision requires `dio` flash mode to prevent crashing, and explicit DTR/RTS assertion to wake up the internal USB CDC interface.

```ini
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
```

### 6.3. Host Python Daemon (`telemetry_stream.py`)
Parses the LHM JSON endpoint with Basic Auth and pushes payloads to the COM port.

```python
import urllib.request
import json
import serial
import time
import sys
import base64

# --- Configuration ---
COM_PORT = 'COM3'
BAUD_RATE = 115200
POLL_RATE_SEC = 2.0
LHM_URL = "http://localhost:8085/data.json"
AUTH_USER = "sffmonitor"
AUTH_PASS = "sffmonitor"

def find_sensors(node, metrics):
    """Recursively traverse the LHM JSON tree to extract values."""
    if "Text" in node and "Value" in node:
        text = node["Text"]
        value = node["Value"]

        # 1. Match CPU Package Temperature
        if "CPU Package" in text and "°C" in value:
            try:
                num = float(value.replace(",", ".").split()[0])
                metrics['temp'] = f"{int(num):02d}"
            except ValueError: pass
        
        # 2. Match Fan RPM
        elif "Fan" in text and "RPM" in value:
            try:
                num = int(value.replace(",", "").split()[0])
                if num > 0 and metrics['rpm'] == "0000":
                    metrics['rpm'] = f"{num:04d}"
            except ValueError: pass

    # Recurse through hardware children
    if "Children" in node:
        for child in node["Children"]:
            find_sensors(child, metrics)

def main():
    # 1. Initialize Serial Connection
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        ser.dtr = True # Mandatory for ESP32-C6 Native USB
        ser.rts = True
        print(f"[+] Serial connection established on {COM_PORT}")
    except serial.SerialException as e:
        print(f"[-] FATAL: Could not open {COM_PORT}. {e}")
        sys.exit(1)

    print(f"[*] Connecting to LHM Web Server at {LHM_URL}...")
    
    # Pre-compute Base64 HTTP Basic Auth string
    auth_str = f"{AUTH_USER}:{AUTH_PASS}"
    auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
    
    # 2. Main Telemetry Loop
    while True:
        try:
            metrics = {'temp': "00", 'rpm': "0000"}
            
            # Request JSON payload with Auth Header
            req = urllib.request.Request(LHM_URL)
            req.add_header("Authorization", f"Basic {auth_b64}")
            
            with urllib.request.urlopen(req, timeout=1) as response:
                data = json.loads(response.read().decode())
                find_sensors(data, metrics)

            # Construct Payload: <T:XX,R:XXXX>
            payload = f"<T:{metrics['temp']},R:{metrics['rpm']}>\n"
            ser.write(payload.encode('utf-8'))
            print(f"Tx: {payload.strip()}")

        except KeyboardInterrupt:
            print("\n[*] Terminating daemon.")
            ser.close()
            sys.exit(0)
        except Exception as e:
            print(f"[-] Data Extraction Error: {e}")
        
        time.sleep(POLL_RATE_SEC)

if __name__ == "__main__":
    main()
```

### 6.4. Hardware Validation Firmware (`src/main.cpp`)
Main rendering pipeline. Initializes with a status message and clears the buffer upon receipt of the first valid payload.

```cpp
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
String inputString = "";
boolean stringComplete = false;
int currentTemp = 0;
int currentRPM = 0;
boolean firstPayloadReceived = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize graphics pipeline
  lcd.init();
  lcd.setRotation(1); 
  lcd.setBrightness(128); 
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
  // 1. Ingest Serial Stream
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>') {
      stringComplete = true;
    }
  }

  // 2. Parse Payload & Render
  if (stringComplete) {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0) {
      
      int tIndex = inputString.indexOf("T:");
      int rIndex = inputString.indexOf("R:");
      int commaIndex = inputString.indexOf(",");
      int closeIndex = inputString.indexOf(">");

      if (tIndex != -1 && rIndex != -1) {
        // Clear the initial setup text on the very first successful read
        if (!firstPayloadReceived) {
          lcd.fillScreen(TFT_BLACK);
          firstPayloadReceived = true;
        }

        String tempStr = inputString.substring(tIndex + 2, commaIndex);
        String rpmStr = inputString.substring(rIndex + 2, closeIndex);
        
        currentTemp = tempStr.toInt();
        currentRPM = rpmStr.toInt();

        // Render Data 
        lcd.setTextSize(3);
        
        // Temperature Block
        lcd.setCursor(10, 30); 
        lcd.setTextColor(TFT_ORANGE, TFT_BLACK); 
        lcd.printf("CPU: %02d C  ", currentTemp);

        // Fan RPM Block
        lcd.setCursor(10, 80); 
        lcd.setTextColor(TFT_CYAN, TFT_BLACK);
        lcd.printf("FAN: %04d RPM  ", currentRPM);
      }
    }
    
    // 3. Reset Buffer
    inputString = "";
    stringComplete = false;
  }
}
```