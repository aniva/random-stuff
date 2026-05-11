# Project: 9L SFF PC Build & Migration
**Author:** Aniva
**Date:** May 11, 2026

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
| **Processor** | Intel Core i5-14400 |
| **CPU Cooler** | Noctua NH-L9i-17xx Premium Low-Profile (Brown) |
| **Memory** | 32GB (2x16GB) DDR4 @ 3200 MHz (XMP Profile Active) |
| **Storage** | 512GB Samsung PM991 NVMe M.2 / 2x 1TB Crucial MX500 SATA SSD |
| **GPU** | NVIDIA GeForce GTX 1650 SUPER (ASUS ROG STRIX 4G) |
| **Power Supply** | FSP Dagger Pro 850W SFX 3.1 |
| **Telemetry Display** | Waveshare ESP32-C6 1.47inch Touch Display (172×320, CH343 UART Bridge) |

### 3.1. Hardware Acceleration Pipeline (Insta360 Studio)
* **Primary Graphics Adapter (UEFI):** `[PCIE1]`. Forces 120Hz display output and NVENC hardware encoding.
* **IGPU Multi-Monitor (UEFI):** `[Enabled]`. Exposes Intel Quick Sync Video (QSV) for HEVC/H.265 timeline decoding.

## 4. Pending Actions
* [ ] **GPU Upgrade Execution:** Procure a sub-252mm NVIDIA GPU optimized for Insta360 Studio and native 120Hz display output via HDMI 2.1.
* [ ] **NVMe Thermal Mitigation:** Procure and install a low-profile (12mm) aluminum block heatsink (e.g., Thermalright M.2 2280 TYPE AB) to reduce Samsung PM991 ambient heat soak.

## 5. Telemetry & Hardware Monitoring Architecture
* **Microcontroller:** Waveshare ESP32-C6 Development Board. 
* **Firmware Stack:** C++ compiled via PlatformIO. Uses `LovyanGFX` for ST7789 display driving. UI follows a RobCo/Fallout terminal aesthetic (Green on Black) featuring a 128x128px Vault Boy boot logo and 32x32px dynamic hardware icons. Data arrays are explicitly offloaded to a dedicated header file (`bitmaps.h`) to optimize compilation. Hardware parameters are isolated in a centralized `config.h` configuration header.
* **Ambient Sensors:** I2C bus deployed on GPIO 0 (SDA) and GPIO 1 (SCL) supporting AHT20 and BMP280 modules.

### 5.1. Hardware Zero-Latency Status Indicators (Opto-Isolation)
To bypass software polling delays, disk activity and power states are wired directly from the motherboard to the ESP32-C6 via hardware optocouplers. The architecture strictly utilizes **physically isolated single-channel PC817 optocouplers** (e.g., ACEIRMC/Micro Traders) to prevent ground plane cross-talk. Isolation jumpers MUST be removed. 

* **Module 1 (HDD):** Motherboard `HDLED+/-` to Input. ESP32 `3.3V/GND/GPIO 4` to Output.
* **Module 2 (PWR):** Motherboard `PLED+/-` to Input. ESP32 `3.3V/GND/GPIO 5` to Output.

### 5.2. Host Infrastructure & Geospatial Dimming
* **Hardware Monitoring Engine:** LibreHardwareMonitor (LHM) with Web Server on Port `8085`.
* **Host Daemon:** Python script (`telemetry_stream.py`) queries LHM JSON. 
* **Dynamic Dimming:** The host daemon utilizes the `astral` library to calculate local sunset/sunrise for Mississauga, ON. The script appends a brightness target (`B:255` or `B:30`) to the serial payload based on configurable hour offsets from the solar events.
* **Service Deployment:** Executed silently via Windows Scheduled Task (`SFF_Telemetry_Daemon`) running with Highest Privileges at User Logon. The task utilizes an explicit `PT30S` (30-second) delay to bypass USB enumeration race conditions. The task targets an isolated PlatformIO python environment to prevent global dependency conflicts.

### 5.3. Hardware Quirks & Serial Protocol
* **CH343 UART Bridge Auto-Reset Circuit:** The Waveshare ESP32-C6 uses a CH343 chip where the DTR and RTS lines are physically wired to the ESP32's `EN` and `IO0` pins. Asserting these lines high triggers the auto-reset circuit, throwing the chip into Download Mode and halting the CPU.
* **PySerial "Instant Open" Trap:** In Python, passing the COM port directly into the `serial.Serial()` constructor instantaneously opens the port with default `DTR=True`. The serial object MUST be instantiated empty, the DTR/RTS lines explicitly disabled, and then manually opened via `.open()`.
* **Serial Buffer Poisoning:** The Python daemon appends a newline (`\n`) to transmit payloads. The ESP32 C++ parser is explicitly programmed to flush the `inputString` buffer upon receiving the `<` character and ignore all invisible carriage returns to prevent offset string corruption.
* **Graceful Standby State Machine:** Due to the CH343 UART bridge supplying constant 5V standby power even when the host PC shuts down, standard `!Serial` hardware watchdogs induce boot-loops. The firmware implements an 8000ms software stopwatch. If data transmission ceases, the UI gracefully downgrades to a dim, offline aesthetic while maintaining real-time ambient sensor reads.

## 6. Code Infrastructure (Truncated Reference)

### 6.1. Python Host Daemon (`telemetry_stream.py`)
Features isolated instantiation to prevent DTR hardware spikes.

```python
def main():
    serPort = None
    while serPort is None:
        try:
            # CRITICAL FIX: Instantiate without opening to prevent DTR spike
            serPort = serial.Serial()
            serPort.port = COM_PORT
            serPort.baudrate = BAUD_RATE
            serPort.timeout = 1
            serPort.dtr = False
            serPort.rts = False
            serPort.open() # Safely open with transistors disabled
        except serial.SerialException:
            time.sleep(5.0)

    # [ ... TRUNCATED WMI/HTTP SENSOR PARSING ... ]
'''

### 6.2. PowerShell Diagnostic Injector (`test_payload.ps1`)
Used strictly for bypassing the Python daemon to validate hardware display rendering.

'''powershell
try {
    $serial = New-Object System.IO.Ports.SerialPort $Port, 115200, 'None', 8, 'One'
    # CRITICAL: Bypasses the CH343 Auto-Reset Transistor Circuit
    $serial.DtrEnable = $false
    $serial.RtsEnable = $false
    
    $serial.Open()
    Start-Sleep -Milliseconds 500  
    $serial.Write($payload)        
    Start-Sleep -Milliseconds 100 
    $serial.Close()
}
catch { Write-Error "Target port $Port is locked." }
'''

### 6.3. ESP32 Firmware (`src/main.cpp`)
Main rendering loop isolates invisible characters and integrates the offline stopwatch.

'''cpp
  // 1. Serial Ingestion & Buffer Sanitization
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '<') { inputString = "<"; } 
    else if (inChar != '\n' && inChar != '\r') { inputString += inChar; }
    if (inChar == '>') stringComplete = true;
  }

  // 2. State Timeout Logic
  unsigned long currentMillis = millis();
  if (isOnline && (currentMillis - lastPayloadTime > offlineTimeoutMs)) {
    isOnline = false;
    forceRedraw = true; 
    lcd.setBrightness(standbyBrightness); // Reverts to PIP-Boy aesthetic
  }
'''