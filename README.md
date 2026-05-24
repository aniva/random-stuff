# Aniva SFF & Slicer Workspace (`random-stuff`)

Welcome to my personal monorepo hosting custom hardware designs, 3D printing profiles, and micro-controller telemetry integrations.

---

## Monorepo Projects

This workspace contains two primary projects: **QIDI Studio Slicer Automation** and the **Aniva SFF01 Custom 9L Chassis**.

### 1. 🖨️ [QIDI Studio Profile Automation & Settings](qidi-studio/)
A workspace dedicated to version-controlling and automating [QIDI Studio](https://github.com/QIDITECH/QIDIStudio) (Orca Slicer-based) printer, filament, and process profiles.
* **AppData Linker:** Bridges your local Windows `%AppData%\QIDIStudio\user\default` profile paths to this Git repo using a custom symlink script (`prepare_windows.cmd`).
* **Advanced Material Settings:** Houses calibrated filament profiles (e.g., temperatures, flow rates, retraction parameters) optimized for structural fabrication.
* **Agentic Support:** Standardized JSON structure allowing AI agents to generate or tweak profiles programmatically.
* **Documentation:** Read more in the [QIDI Studio README](qidi-studio/README.md).

---

### 2. 📐 [Aniva SFF01: CAD Fabrication Files](sff_case_9L_01/cad_files/)
Digital design and structural parts for the **Aniva SFF01** — an open-source, modular ~9L Small Form Factor PC chassis.
* **PC-PBT Material Tuning:** Recesses and captive nut slots are specifically dimensioned to accommodate the rigidity and yield stress of Polymaker PC-PBT to eliminate styrene off-gassing.
* **Modular Panel Design:** Built for M3 mechanical fasteners with precise dimensional clearance for top active exhaust, long GPU architectures, and motherboard tray cabling.
* **Documentation:** Read more in the [CAD README](sff_case_9L_01/cad_files/README.md).

---

### 📟 [Aniva SFF01: Microcontroller Telemetry Sub-System](sff_case_9L_01/telemetry_display/)
Firmware, software, and schematics for the front-panel hardware monitor integrated into the Aniva SFF01 chassis.
* **ESP32-C6 Firmware (C++):** Arduino-framework firmware using the LovyanGFX library for the Waveshare 1.47" touch LCD. Features dynamic I2C bus-hopping for dual AHT20 ambient sensors and analog motherboard LED activity monitoring.
* **Host Telemetry Daemon (Python):** Background script that fetches CPU/GPU/SSD thermals and loads using the LibreHardwareMonitor HTTP JSON API and pushes serial data to the display over internal USB.
* **Solar Dimming:** Auto-dims the display at night using astral calculations based on local coordinates.
* **Documentation:** Read more in the [Telemetry Display README](sff_case_9L_01/telemetry_display/README.md).