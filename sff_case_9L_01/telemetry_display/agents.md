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
    * Localhost Web Server explicitly enabled on Port `8085`[cite: 1].
    * HTTP Basic Authentication active (Credentials: `sffmonitor` / `sffmonitor`)[cite: 1].
* **Python Environment:** Global Windows Python 3.14 installation required. Executed via the `pythonw.exe` background launcher.
* **Host Daemon:** Python script (`telemetry_stream.py`) querying the LHM JSON namespace. Extracts CPU/GPU metrics and transmits formatted binary strings (e.g., `<T:XX,R:XXXX,D:XX>`) to the ESP32-C6 over the virtual USB CDC COM port every 2.0s[cite: 1].

### 5.2. Automated Service Deployment (Production)
To ensure the telemetry stream is resilient and starts automatically without a visible console window, the system uses a **Windows Scheduled Task**[cite: 2].

* **Task Name:** `SFF_Telemetry_Daemon`.
* **Execution Identity:** Runs with **Highest Privileges** (Admin) to ensure compatibility with ASRock motherboard sensor access[cite: 1, 2].
* **Trigger:** Executes at **User Logon**[cite: 2].
* **Pre-Flight Delay:** The task includes a built-in **5-second delay** to allow the LHM Web Server and network stack to initialize before the serial stream begins[cite: 1, 2].

**Management Commands (Administrator PowerShell):**
* **Install/Update:** `powershell -ExecutionPolicy Bypass -File ".\install_task.ps1"`[cite: 2].
* **Manual Start:** `Start-ScheduledTask -TaskName "SFF_Telemetry_Daemon"`[cite: 2].
* **Check Status:** `Get-ScheduledTask -TaskName "SFF_Telemetry_Daemon"`[cite: 2].

## 6. ESP32-C6 Display Recovery & Source Code
Required execution paths and source code configurations for the telemetry array.

### 6.1. Flash Memory Erase
If the microcontroller is actively crashing, hold the physical **BOOT** button, short-press **RST**, and release **BOOT** to force Download Mode. Execute the following to wipe the flash memory:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase
```

### 6.2. PlatformIO Configuration (`platformio.ini`)
The v0.2 hardware revision requires `dio` flash mode to prevent crashing, and explicit DTR/RTS assertion to wake up the internal USB CDC interface[cite: 1].

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