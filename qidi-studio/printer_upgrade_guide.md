# QIDI Q2 Firmware Upgrade & Configuration Recovery Guide

This guide documents the procedures for maintaining custom printer configurations, recovering settings after official QIDI OTA firmware updates, and verifying real-time log streaming to **`ai-box`** (`192.168.1.5`).

---

## 1. Overview & Architecture

All printer configurations, safety macros, and custom hardware settings are version-controlled in this Git repository under `printer_config/`.

### Core Custom Configurations Maintained:
* **Smart Silent Electronics Fan (`board_fan`):** Runs at 35% power when printing/homing; automatically shuts **COMPLETELY OFF (0% / Silent)** 30 seconds after printing completes (`idle_timeout: 30`, `idle_speed: 0.0`).
* **Host CPU Temperature Sensor:** Integrated Host SBC thermal monitoring (`/sys/class/thermal/thermal_zone0/temp`).
* **Smart Exhaust Fan Control:** Capped at 25% max speed during active prints (`gcode_macro.cfg`) to protect chamber temperatures while venting fumes; auto-purges at 100% for 120s post-print.
* **Filament Unload Crash Fix:** Intercepts external spool `E_UNLOAD` commands in `box.cfg` to prevent `Unknown config object '-1'` Klipper crashes.
* **MCU Serial Mapping:** Permanent MCU USB serial ID mapping (`MCU_ID.cfg`).

---

## 2. Firmware Upgrade Recovery Procedure

When QIDI releases an Official OTA Firmware Update (e.g. `QD_Q2_01.01.02.04`), the update installer may reset stock configuration files on the printer.

To **restore all custom settings and log streaming** in a single step, run:

```bash
python3 scripts/sync_printer.py push
```

### What `sync_printer.py push` Executes:
1. **Configuration Comparison:** Compares local Git `printer_config/` files against the printer and uploads any modified configs via Moonraker API.
2. **Log Streaming Audit:** Verifies that `/etc/rsyslog.d/50-remote.conf` on the printer is active and forwarding syslog entries to `ai-box` (`192.168.1.5`). If missing or reset by the firmware update, it **automatically re-applies the rsyslog config and restarts rsyslog**.
3. **Klipper Service Restart:** Restarts Klipper cleanly to activate all custom settings.

---

## 3. Remote Log Streaming to `ai-box` (`192.168.1.5`)

System and daemon logs from the QIDI Q2 printer are streamed over UDP Port 514 to the central log server `ai-box`.

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
├── qidi-printer.log        # Custom printer events & status messages
├── klipper_mcu.log         # Microcontroller serial event logs
├── main.log                # Primary system daemon logs
├── sshd.log                # SSH access logs
└── systemd.log             # Systemd service logs
```

### Viewing Live Logs on `ai-box`:
```bash
# View live printer log stream
ssh me@192.168.1.5 "tail -f /var/log/remote/qidiq2/qidi-printer.log"

# View live system logs
ssh me@192.168.1.5 "tail -f /var/log/qidiq2/main.log"
```

---

## 4. Git Repository Maintenance

Always commit configuration changes after testing updates on the printer:

```bash
git add printer_config/ scripts/sync_printer.py printer_upgrade_guide.md
git commit -m "Update printer config and sync scripts"
```
