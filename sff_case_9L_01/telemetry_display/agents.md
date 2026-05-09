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
    * Localhost Web Server explicitly enabled on Port `8085`[cite: 8].
    * HTTP Basic Authentication active (Credentials: `sffmonitor` / `sffmonitor`)[cite: 8].
* **Python Environment:** Global Windows Python 3.14 installation required. Executed via the `pythonw.exe` background launcher.
* **Host Daemon:** Python script (`telemetry_stream.py`) querying the LHM JSON namespace. Extracts CPU/GPU metrics and transmits formatted binary strings (e.g., `<T:XX,R:XXXX,G:XX,M:XX,C:XX,L:XX>`) to the ESP32-C6 over the virtual USB CDC COM port every 2.0s[cite: 8].

### 5.2. Automated Service Deployment (Production)
To ensure the telemetry stream is resilient and starts automatically without a visible console window, the system uses a **Windows Scheduled Task**[cite: 8].

* **Task Name:** `SFF_Telemetry_Daemon`.
* **Execution Identity:** Runs with **Highest Privileges** (Admin) to ensure compatibility with ASRock motherboard sensor access[cite: 8].
* **Trigger:** Executes at **User Logon**[cite: 8].

**Management Commands (Administrator PowerShell):**
* **Install/Update:** `powershell -ExecutionPolicy Bypass -File ".\install_task.ps1"`[cite: 8].
* **Manual Start:** `Start-ScheduledTask -TaskName "SFF_Telemetry_Daemon"`[cite: 8].
* **Check Status:** `Get-ScheduledTask -TaskName "SFF_Telemetry_Daemon"`[cite: 8].

### 5.3. Hardware Zero-Latency Disk IO Indicator
To bypass the 2.0s polling delay of the software daemon, disk activity is wired directly from the motherboard HDD LED header to the ESP32-C6 via a DAOKI PC817 2-Channel Optocoupler Isolation Board.
*   **Motherboard `HDD LED +`** -> Module `IN1`
*   **Motherboard `HDD LED -`** -> Module `G` (Input Side)
*   **ESP32 `3.3V`** -> Module `V1`
*   **ESP32 `GND`** -> Module `G` (Output Side)
*   **ESP32 `GPIO 4`** -> Module `O1` (Output Signal)

## 6. ESP32-C6 Source Code & Host Daemon
Required execution paths and source code configurations for the telemetry array.

### 6.1. Flash Memory Erase
If the microcontroller is actively crashing, force Download Mode and execute the following:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase
```

### 6.2. PlatformIO Configuration (`platformio.ini`)
The v0.2 hardware revision requires `dio` flash mode to prevent crashing, and explicit DTR/RTS assertion to wake up the internal USB CDC interface[cite: 8].

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
Parses the LHM JSON endpoint. Fan extraction logic iterates through all fan headers dynamically and averages the RPM to provide a single, unified chassis cooling metric.

```python
import urllib.request
import json
import serial
import time
import sys
import base64
import socket

# --- Configuration ---
COM_PORT = 'COM3'
BAUD_RATE = 115200
POLL_RATE_SEC = 2.0
LHM_URL = "http://localhost:8085/data.json"
LHM_PORT = 8085
authUser = "sffmonitor"
authPass = "sffmonitor"

def check_lhm_server():
    """Verify LHM web server is actually listening before starting."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        return s.connect_ex(('localhost', LHM_PORT)) == 0

def find_sensors(node, metrics):
    if "Text" in node and "Value" in node:
        text = node["Text"]
        value = node["Value"]
        
        if "CPU Package" in text and "°C" in value:
            metrics['temp'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "GPU Core" in text and "°C" in value and "/gpu-nvidia/" in node.get("SensorId", ""):
            metrics['gpu_t'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        
        # Chassis Fan Averaging Logic
        elif "Fan" in text and "RPM" in value:
            try:
                rpm_val = int(value.replace(',', '').split()[0])
                if rpm_val > 0:
                    metrics['fan_list'].append(rpm_val)
            except ValueError: pass
            
        elif "Composite Temperature" in text and "°C" in value:
            metrics['nvme'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "CPU Total" in text and "%" in value:
            metrics['cpu_l'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "GPU Core" in text and "%" in value and "/gpu-nvidia/" in node.get("SensorId", ""):
            metrics['gpu_l'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"

    if "Children" in node:
        for child in node["Children"]:
            find_sensors(child, metrics)

def connect_serial():
    while True:
        try:
            ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            ser.dtr = True 
            ser.rts = True
            print(f"[+] Serial connection established on {COM_PORT}")
            return ser
        except (serial.SerialException, PermissionError):
            print(f"[-] Waiting for {COM_PORT}... Is the USB unplugged?")
            time.sleep(2)

def main():
    print(f"[*] Checking for LHM server on port {LHM_PORT}...")
    while not check_lhm_server():
        print("[-] LHM Web Server not detected.")
        time.sleep(5)

    ser = connect_serial()
    authB64 = base64.b64encode(f"{authUser}:{authPass}".encode('ascii')).decode('ascii')
    
    while True:
        try:
            metrics = {
                'temp': "00", 'gpu_t': "00", 'nvme': "00", 
                'cpu_l': "00", 'gpu_l': "00", 'fan_list': []
            }
            
            req = urllib.request.Request(LHM_URL)
            req.add_header("Authorization", f"Basic {authB64}")
            try:
                with urllib.request.urlopen(req, timeout=1) as response:
                    data = json.loads(response.read().decode())
                    find_sensors(data, metrics)
            except Exception as e:
                print(f"[-] HTTP Error: {e}")
                time.sleep(POLL_RATE_SEC)
                continue

            # Calculate Fan Average
            avg_rpm = sum(metrics['fan_list']) // len(metrics['fan_list']) if metrics['fan_list'] else 0
            
            payload = f"<T:{metrics['temp']},R:{avg_rpm:04d},G:{metrics['gpu_t']},M:{metrics['nvme']},C:{metrics['cpu_l']},L:{metrics['gpu_l']}>\n"
            
            try:
                ser.write(payload.encode('utf-8'))
            except Exception as e:
                ser.close()
                ser = connect_serial() 

        except KeyboardInterrupt:
            ser.close()
            sys.exit(0)
        
        time.sleep(POLL_RATE_SEC)

if __name__ == "__main__":
    main()
```

### 6.4. Hardware Validation Firmware (`src/main.cpp`)
Main rendering pipeline. Features landscape/portrait configuration, dynamic unified color coding based on thermal/load states, whitespace buffer padding to prevent ghosting, and hardware-level optocoupler interrupts for disk IO.

```cpp
#include <Arduino.h>
#include <LovyanGFX.hpp>

#define HDD_LED_PIN 4 

// --- Display Configuration ---
// Set to true for Landscape, false for Portrait (USB on top)
const bool IS_LANDSCAPE = false;

class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 _panel_instance;
  lgfx::Bus_SPI _bus_instance;
  lgfx::Light_PWM _light_instance;

public:
  LGFX(void) {
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
  pinMode(HDD_LED_PIN, INPUT);
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

void loop() {
  // 1. Hardware Disk IO
  int diskState = digitalRead(HDD_LED_PIN);
  int dotX = IS_LANDSCAPE ? 300 : 150; 
  
  if (diskState == LOW) {
    lcd.fillCircle(dotX, 10, 5, TFT_GREEN);
  } else {
    lcd.fillCircle(dotX, 10, 5, TFT_BLACK);
  }

  // 2. Serial Ingestion
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '>') stringComplete = true;
  }

  // 3. Payload Parsing
  if (stringComplete) {
    if (inputString.startsWith("<") && inputString.indexOf(">") > 0) {
      int t = getValueByTag(inputString, "T:", ',');
      int r = getValueByTag(inputString, "R:", ',');
      int g_t = getValueByTag(inputString, "G:", ',');
      int m = getValueByTag(inputString, "M:", ',');
      int c_l = getValueByTag(inputString, "C:", ','); 
      int g_l = getValueByTag(inputString, "L:", '>'); 

      if (t != -1 && r != -1) {
        if (!firstPayloadReceived) {
          lcd.fillScreen(TFT_BLACK);
          firstPayloadReceived = true;
        }

        lcd.setTextSize(2);

        if (IS_LANDSCAPE) {
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
        } else {
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
```