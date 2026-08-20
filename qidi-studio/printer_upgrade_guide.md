# QIDI Q2 Firmware Upgrade, Fan Architecture & Recovery Guide

This guide documents the procedures for maintaining custom printer configurations, troubleshooting thermal/fan hardware mappings, recovering settings after official QIDI OTA firmware updates, and verifying real-time log streaming to **`ai-box`** (`192.168.1.5`).

---

## 1. Hardware Pin & Fan Mapping Reference

The QIDI Q2 motherboard and toolhead use the following fan and heater pin assignments:

| Fan / Device | Pin | Klipper Type | Configuration & Function |
| :--- | :---: | :---: | :--- |
| **`chamber_fan`** | **`PB14`** | `controller_fan` | **PTC Heater Blower Fan:** Linked to `heater: chamber`. Automatically spins at 100% (4,400 RPM) whenever the chamber heater is active to blow heat into the chamber and prevent PTC ceramic core overheating. |
| **`board_fan`** | **`PA9`** | `controller_fan` | **Mainboard Electronics Fan:** Runs at 35% power during homing/printing to cool stepper drivers; automatically shuts **COMPLETELY OFF (0% / Silent)** 30 seconds after print finishes (`idle_timeout: 30`, `idle_speed: 0.0`). |
| **`hotend_fan`** | **`THR:PA11`** | `heater_fan` | **Extruder Heatsink Fan:** Linked to `heater: extruder`. Automatically turns ON (16,000 RPM) whenever nozzle temperature exceeds 50°C. |
| **`cooling_fan`** | **`THR:PA8`** | `fan_generic` | **Part Cooling Fan:** Controlled dynamically by the slicer during printing. |
| **`chamber_circulation_fan`** | **`PA10`** | `fan_generic` | **Duct Vent / Rear Exhaust Fan:** Controlled via `M106 P3` for chamber air exchange and post-print fume purging. |
| **`auxiliary_cooling_fan`** | **`PB15`** | `fan_generic` | **Side Auxiliary Cooling Fan:** Controlled via `M106 P2`. |

---

## 2. Thermal Protection Sensors & RCA

### Chamber Thermal Protection (`PA2`):
* **Sensor Type:** `NTC 100K MGB18-104F39050L32` attached directly to the ceramic PTC heating element core.
* **Configured Threshold:** `min_temp: -100`, `max_temp: 200`
* **RCA of Previous Crashes:** If `PB14` blower fan is not actively linked to `heater: chamber`, the ceramic PTC element will heat up without airflow, exceeding 180°C and triggering Klipper's `ADC out of range` safety shutdown. When `PB14` is running at 100%, the PTC core stabilizes at **~65°C–78°C** under full heating load.

### Host SBC CPU Temperature:
* **Sensor Type:** `temperature_host`
* **Sensor Path:** `/sys/class/thermal/thermal_zone0/temp`
* **Normal Operating Range:** 45°C – 75°C.

---

## 3. Firmware Upgrade Recovery Procedure

When QIDI releases an Official OTA Firmware Update (e.g. `QD_Q2_01.01.02.04`), the update installer may reset stock configuration files on the printer.

To **restore all custom settings and log streaming** in a single step from your terminal:

```bash
python3 scripts/sync_printer.py push
```

### What `sync_printer.py push` Executes:
1. **Configuration Comparison:** Compares local Git `printer_config/` files against the printer and uploads any modified configs via Moonraker API.
2. **Log Streaming Audit:** Verifies that `/etc/rsyslog.d/50-remote.conf` on the printer has `imfile` active for `klippy.log` and `moonraker.log`, and is forwarding syslog entries to `ai-box` (`192.168.1.5`). If missing or reset by the firmware update, it **automatically re-applies the rsyslog config and restarts rsyslog**.
3. **Klipper Service Restart:** Restarts Klipper cleanly to activate all custom settings.

---

## 4. Remote Log Streaming to `ai-box` (`192.168.1.5`)

System, Klipper, and Moonraker logs from the QIDI Q2 printer are streamed in real time over UDP Port 514 to the central log server `ai-box`.

### Log Paths on `ai-box`:
* **Primary Target Directory:**
  ```bash
  /var/log/remote/qidiq2/
  ```
* **Convenient Shortcut:**
  ```bash
  /var/log/qidiq2 -> /var/log/remote/qidiq2
  ```

### Live Log Files Streamed:
```bash
/var/log/remote/qidiq2/
├── klippy.log              # Real-time Klipper firmware engine logs & telemetry
├── moonraker.log           # Real-time Moonraker API & web socket logs
├── qidi-printer.log        # Custom printer events & status messages
├── klipper_mcu.log         # Microcontroller serial event logs
├── main.log                # Primary system daemon logs
├── sshd.log                # SSH access logs
└── systemd.log             # Systemd service logs
```

### Viewing Live Logs on `ai-box`:
```bash
# Follow live Klippy engine logs on ai-box
ssh me@192.168.1.5 "tail -f /var/log/remote/qidiq2/klippy.log"

# Follow live Moonraker API logs on ai-box
ssh me@192.168.1.5 "tail -f /var/log/remote/qidiq2/moonraker.log"
```

---

## 5. Storage Maintenance (Clearing Old G-Codes)

Accumulating dozens of large `.gcode.3mf` files on the printer can cause Moonraker's background metadata scanner (`metadata.py`) to consume high CPU and stall upload queues after reboots.

To purge old print files and thumbnails from the printer:
```bash
ssh mks@192.168.1.27 "echo makerbase | sudo -S rm -rf /home/qidi/printer_data/gcodes/* /home/qidi/printer_data/.cache/*"
```
