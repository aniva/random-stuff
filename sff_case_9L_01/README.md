# Project: Aniva SFF01 (Custom 9L SFF Chassis)

An open-source SFF chassis design (digital CAD files and fabricated physical units) created to help fellow builders. This project showcases a unique hardware and software integration as an art project for delight (featuring a Pip-Boy themed display), establishing an independent design footprint through customized structural dimensions, optimized thermal headroom, and an integrated hardware telemetry screen.

## 1. Project Objectives
* **Open Source Community:** Provide free digital CAD files (STEP/STL) to help the SFF building community create and modify their own ~9L enclosures.
* **Art & Delight:** Showcase unique hardware and software integration, primarily through a custom Pip-Boy themed telemetry display.
* **Custom Architecture:** Ensure a wholly original, ground-up design architecture tailored for optimal structural integrity and thermal management.
* **Hardware Telemetry Integration:** Natively integrate a Waveshare ESP32-C6 1.47-inch touch display into the front panel to monitor system metrics (thermals, loads, fan speeds).

## 2. Custom Fabrication Details
* **Chassis Material:** Polymaker PC-PBT. The original ABS iteration was scrapped and fully re-printed to permanently eliminate toxic styrene off-gassing (VOCs) experienced under ambient internal temperatures exceeding 50°C. PC-PBT provides zero VOC emissions under load, high impact resistance, and a Glass Transition Temperature ($) of ~110°C.
* **Assembly Architecture:** Modular panels secured via M3 bolts. Shapr3D captive nut recesses calibrated to 5.65mm - 5.70mm to accommodate the mechanical rigidity and yield stress of the PC-PBT matrix.
* **Dimensional Architecture:**
    * **Height (H):** Engineered with precise vertical clearance to natively integrate top-mounted active exhaust fans.
    * **Width (W):** Optimized interior width provides exceptional cable routing and thermal clearance beneath the motherboard tray.
    * **Length (L):** Specifically dimensioned length accommodates extended GPU architectures while natively supporting a front-mounted SSD layout.
* **Power Delivery:** Custom 90-degree IEC C13 plug using AC-18 internal contacts and 18AWG flexible silicone wire.
* **Custom Cables:** DIY shortening of FSP Dagger Pro 850W stock ribbon cables to resolve volumetric interference.

## 3. Microcontroller Telemetry Integration
Real-time environmental and hardware monitoring is achieved via an integrated microcontroller sub-system mounted directly to the chassis front panel.
* **Microcontroller:** Waveshare ESP32-C6 Development Board.
* **Display Output:** 1.47-inch integrated IPS LCD Touch Display (172×320 resolution, JD9853 driver).
* **Firmware (Device):** Written in C++ utilizing the LovyanGFX graphics library, compiled via PlatformIO in VSCode. Device is configured to boot directly into USB CDC mode (ARDUINO_USB_CDC_ON_BOOT=1) to act as a dedicated serial receiver.
* **Host Daemon (Windows):** A Python script running continuously as a background service on Windows 11. It extracts CPU, GPU, SSD temperatures, fan speeds, and system loads via the LibreHardwareMonitor HTTP JSON API and pushes a formatted payload string (e.g., <T:55,R:2100,...>) to the ESP32-C6 over the internal USB header connection.

## 4. Repository Structure
* **📁 [cad_files/](cad_files/)** — Collection of STEP and STL files for 3D printing and CAD modification. See [CAD README](cad_files/README.md).
* **📁 [telemetry_display/](telemetry_display/)** — PlatformIO firmware, Python host daemon, and wiring documentation for the Pip-Boy telemetry display. See [Telemetry Display README](telemetry_display/README.md).


