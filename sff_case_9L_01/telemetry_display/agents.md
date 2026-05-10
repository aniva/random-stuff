# Project: 9L SFF PC Build & Migration
**Author:** Aniva
**Date:** May 10, 2026

## 1. Project Overview & Strategic Objectives
Migration of hardware from an A01 Aluminum Mini-ITX chassis to a custom ~9L SFF enclosure. 
* **Commercial Productization:** Engineer and market a distinct, proprietary SFF chassis design.
* **Visual Optimization (120Hz):** Achieve native 4K @ 120Hz output for an 85" Samsung display.
* **Hardware Acceleration:** Maximize Insta360 Studio timeline scrubbing and export encoding performance.
* **Hardware Telemetry Integration:** Deploy a microcontroller-driven front panel display for real-time thermal monitoring, hardware status indication, and geospatially-aware backlight dimming.

## 2. Custom Fabrication Details
* **Chassis Material (Re-Printed):** Polymaker PC-PBT.
* **Assembly Architecture:** Modular panels secured via M3 bolts. Captive nut recesses calibrated to 5.65mm - 5.70mm in Shapr3D.
* **Dimensional Divergence:** Height increased for top exhaust fans; Width +1mm for routing; Length +10mm (Max GPU limit: ~252mm).
* **Power Delivery:** Custom 90-degree IEC C13 plug interfaces with the PSU. IEC C14 inlet wiring: Green (Ground), Black (Line), White (Neutral).

## 3. Hardware Specifications (Active Build)
| Component | Specification |
| :--- | :--- |
| **Motherboard** | ASRock B760M-ITX/D4 WiFi (UEFI Version 11.02) |
| **Processor** | Intel Core i3-12100 (Pending Migration to i5-14400) |
| **CPU Cooler** | Noctua NH-L9i-17xx Premium Low-Profile (Brown) |
| **Memory** | 32GB (2x16GB) DDR4 @ 3200 MHz (XMP Profile Active) |
| **Storage** | 512GB Samsung PM991 NVMe M.2 / 2x 1TB Crucial MX500 SATA SSD |
| **GPU** | NVIDIA GeForce GTX 1650 SUPER (ASUS ROG STRIX 4G) |
| **Power Supply** | FSP Dagger Pro 850W SFX 3.1 |
| **Telemetry Display** | Waveshare ESP32-C6 1.47inch Touch Display (172×320, v0.2 Hardware Revision) |

### 3.1. Hardware Acceleration Pipeline (Insta360 Studio)
* **Primary Graphics Adapter (UEFI):** `[PCIE1]`. Forces 120Hz display output and NVENC hardware encoding.
* **IGPU Multi-Monitor (UEFI):** `[Enabled]`. Exposes Intel Quick Sync Video (QSV) for HEVC/H.265 timeline decoding.

## 4. Pending Actions
* [ ] **Physical CPU Migration:** Execute swap to Intel Core i5-14400. Adjust PL1/PL2 power limits.
* [ ] **GPU Upgrade Execution:** Procure a sub-252mm NVIDIA GPU optimized for Insta360 Studio and native 120Hz display output via HDMI 2.1.

## 5. Telemetry & Hardware Monitoring Architecture
* **Microcontroller:** Waveshare ESP32-C6 Development Board. 
* **Firmware Stack:** C++ compiled via PlatformIO. Uses `LovyanGFX` for ST7789 display driving. UI follows a RobCo/Fallout terminal aesthetic (Green on Black) featuring a 128x128px Vault Boy boot logo.
* **Ambient Sensors:** I2C bus deployed on GPIO 0 (SDA) and GPIO 1 (SCL) supporting AHT20 and BMP280 modules.

### 5.1. Hardware Zero-Latency Status Indicators (Opto-Isolation)
To bypass software polling delays, disk activity and power states are wired directly from the motherboard to the ESP32-C6 via hardware optocouplers. The architecture strictly utilizes **physically isolated single-channel PC817 optocouplers** (e.g., ACEIRMC/Micro Traders) to prevent ground plane cross-talk. Isolation jumpers MUST be removed. 

* **Module 1 (HDD):** Motherboard `HDLED+/-` to Input. ESP32 `3.3V/GND/GPIO 4` to Output.
* **Module 2 (PWR):** Motherboard `PLED+/-` to Input. ESP32 `3.3V/GND/GPIO 5` to Output.

### 5.2. Host Infrastructure & Geospatial Dimming
* **Hardware Monitoring Engine:** LibreHardwareMonitor (LHM) with Web Server on Port `8085`.
* **Host Daemon:** Python script (`telemetry_stream.py`) queries LHM JSON. 
* **Dynamic Dimming:** The host daemon utilizes the `astral` library to calculate local sunset/sunrise for Mississauga, ON. The script appends a brightness target (`B:255` or `B:30`) to the serial payload based on configurable hour offsets from the solar events.
* **Service Deployment:** Executed silently via Windows Scheduled Task (`SFF_Telemetry_Daemon`) running with Highest Privileges at User Logon.

## 6. Code Infrastructure (Truncated Reference)
*Note: Boilerplate rendering logic, WMI fallbacks, and large hex arrays are omitted for brevity.*

### 6.1. PlatformIO Configuration (`platformio.ini`)
Requires `dio` flash mode for v0.2 hardware and explicit DTR/RTS assertion.

```ini
[env:esp32-c6-devkitc-1]
platform = espressif32
board = esp32-c6-devkitc-1
framework = arduino
monitor_speed = 115200
board_build.flash_mode = dio
monitor_dtr = 1
monitor_rts = 1
build_flags = 
    -D ARDUINO_USB_MODE=1
    -D ARDUINO_USB_CDC_ON_BOOT=1
lib_deps = 
    lovyan03/LovyanGFX@^1.1.16
    adafruit/Adafruit AHTX0@^2.0.5
    adafruit/Adafruit BMP280 Library@^2.6.8
```

### 6.2. Python Host Daemon (`telemetry_stream.py`)
**Dependencies:** `pip install astral pytz wmi pyserial`

```python
from astral import LocationInfo
from astral.sun import sun
import pytz

# --- Dimming Configuration ---
cityData = LocationInfo("Mississauga", "Canada", "America/Toronto", 43.5890, -79.6441)
xOffsetHrs = 1.0  # Hours AFTER sunset to start dimming
yOffsetHrs = 1.0  # Hours BEFORE sunrise to stop dimming
brightnessDay = 255
brightnessNight = 30

def getTargetBrightness():
    tz = pytz.timezone(cityData.timezone)
    now = datetime.now(tz)
    try:
        solarData = sun(cityData.observer, date=now.date(), tzinfo=tz)
        dimStart = solarData["sunset"] + timedelta(hours=xOffsetHrs)
        dimStop = solarData["sunrise"] - timedelta(hours=yOffsetHrs)
        
        if dimStop <= now <= dimStart: return brightnessDay
        else: return brightnessNight
    except Exception: return brightnessDay

# [ ... TRUNCATED LHM PARSING & SERIAL INIT ... ]

def main():
    # [ ... TRUNCATED ... ]
    while True:
        # [ ... TRUNCATED DATA FETCH ... ]
        targetBrightness = getTargetBrightness()
        payloadStr = f"<T:{cpuTemp},R:{fanRpm},G:{gpuTemp},M:{nvmeTemp},C:{cpuLoad},L:{gpuLoad},B:{targetBrightness}>\n"
        serPort.write(payloadStr.encode('utf-8'))
        time.sleep(2.0)
```

### 6.3. ESP32 Firmware (`main.cpp`)
Main rendering loop includes a 10-second payload timeout to revert brightness if the host daemon disconnects.

```cpp
// [ ... TRUNCATED LOVYANGFX INIT & SENSOR SETUP ... ]
// [ ... TRUNCATED 128x128 PIP-BOY BITMAP ARRAY ... ]

unsigned long lastPayloadTime = 0;
const unsigned long PAYLOAD_TIMEOUT = 10000; 
const int DEFAULT_BRIGHTNESS = 128;
bool signalLost = false;

void loop() {
  // 1. Hardware LED Optocoupler Parsing
  int diskState = (analogRead(HDD_LED_PIN) < 3000) ? LOW : HIGH;
  int pwrState  = (analogRead(PWR_LED_PIN) < 3000) ? LOW : HIGH;
  // [ ... TRUNCATED ICON RENDERING ... ]

  // 2. Local Ambient Sensors
  // [ ... TRUNCATED I2C AHT/BMP POLLING ... ]

  // 3. Fallback Brightness Logic
  if (firstPayloadReceived && (millis() - lastPayloadTime > PAYLOAD_TIMEOUT)) {
      if (!signalLost) {
          lcd.setBrightness(DEFAULT_BRIGHTNESS);
          signalLost = true;
      }
  }

  // 4. Serial Ingestion
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>') stringComplete = true;
  }

  if (stringComplete) {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0) {
      // Parse tags
      int t = getValueByTag(inputString, "T:", ',');
      // [ ... TRUNCATED OTHER SENSOR TAGS ... ]
      int b = getValueByTag(inputString, "B:", '>'); 

      if (t != -1) {
        lastPayloadTime = millis();
        signalLost = false;

        if (b != -1) lcd.setBrightness(b);

        if (!firstPayloadReceived) {
          drawBaseLayout(); // Wipes boot screen
          firstPayloadReceived = true;
        }
        // [ ... TRUNCATED TELEMETRY RENDERING ... ]
      }
    }
    inputString = "";
    stringComplete = false;
  }
}
```