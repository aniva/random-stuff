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
| **Telemetry Display** | Waveshare ESP32-C6 1.47inch Touch Display (172×320, WiFi 6 & BT) |

### 3.1. Hardware Acceleration Pipeline (Insta360 Studio)
* **Primary Graphics Adapter (UEFI):** `[PCIE1]`. Forces 120Hz display output and NVENC hardware encoding via the discrete NVIDIA GPU.
* **IGPU Multi-Monitor (UEFI):** `[Enabled]`. Exposes Intel Quick Sync Video (QSV) silicon to the OS for efficient background HEVC/H.265 timeline decoding without overriding the discrete GPU.

## 4. Pending Actions
* [ ] **Physical CPU Migration:** Execute swap to Intel Core i5-14400. Strict adjustment of PL1/PL2 power limits required in UEFI to prevent thermal throttling against the Noctua NH-L9i-17xx.
* [ ] **Front Panel Fabrication:** Measure exact physical tolerances of the Waveshare ESP32-C6 PCB and Type-C port using digital calipers. Execute Shapr3D cuts for flush mount.
* [ ] **GPU Upgrade Execution:** Procure a sub-252mm NVIDIA GPU optimized for Insta360 Studio and native 120Hz display output via HDMI 2.1 (~$300 CAD secondary market). Options: RTX 4060 8GB or RTX 3060 12GB.

## 5. Telemetry & Hardware Monitoring Architecture
* **Microcontroller:** Waveshare ESP32-C6 Development Board.
* **Firmware Stack:** C++ compiled via PlatformIO (pioarduino v3.x core override). Utilizes `LovyanGFX` for hardware-native ST7789 display driving with a 34px X-axis offset memory correction. Configured with `ARDUINO_USB_CDC_ON_BOOT=1` to receive serial payload via COM3.

### 5.1. Host Infrastructure & Deployment
* **Hardware Monitoring Engine:** LibreHardwareMonitor (LHM). 
    * Must be executed as Administrator.
    * WMI Server must be explicitly enabled via `Options -> Run WMI Server` to broadcast kernel-level thermals to the OS.
* **Python Environment:** Global Windows Python 3.14 installation required. Executed via the `py` launcher. Dependencies: `pip install wmi pyserial`.
* **Host Daemon:** Python script (`telemetry_stream.py`) querying the LHM WMI namespace. Extracts CPU Temp/Fan RPM and transmits formatted binary strings (`<T:XX,R:XXXX>`) to the ESP32-C6 over COM3 every 2.0s.
* **Test Automation:** Local PowerShell wrapper (`test_payload.ps1`) constructed for rapid UI payload injection and bounding-box testing within the VS Code terminal.
* **Startup Initialization:** VBScript wrapper (`launch_telemetry.vbs`) configured in Windows `shell:startup` to execute the Python daemon silently (`pythonw.exe`) in the background on user login.

## 6. ESP32-C6 Nuclear Erase & Recovery Protocol
Use these exact commands when the module is stuck in a boot loop (`invalid header: 0xffffffff`), missing the GUI "Erase Flash" button, or when residual software prevents hardware initialization.

### 6.1. Execution
Run this command from the project root (`...\telemetry_display`) in **Windows PowerShell** to wipe the chip entirely:
```bash
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase
```
*Note: If the command fails to connect, hold the **BOOT** button on the back of the module while plugging in the USB to force Download Mode.*

### 6.2. Post-Erase Validation
1. **Manual Cleanup:** Delete the `.pio` folder in the project root to clear corrupted library headers.
2. **Silence Check:** Open the Serial Monitor. The successful erase leaves the chip empty, so absolutely no text should appear.
3. **Hardware Test:** Upload a minimal `digitalWrite` test on GPIO 15 to verify backlight hardware before re-introducing LovyanGFX.

```cpp
#include <Arduino.h>
void setup() {
  Serial.begin(115200);
  pinMode(15, OUTPUT);
}
void loop() {
  digitalWrite(15, HIGH); 
  delay(2000);
  digitalWrite(15, LOW);
  delay(2000);
}
```