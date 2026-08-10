# QIDI Multi-Layer Log & Telemetry Streaming Architecture

This directory contains the daemon and deployment scripts to continuously stream all operational logs, telemetry, micro-step stats, and layer-by-layer print progress from the **QIDI Q2 / Klipper Printer** (`192.168.1.27`) directly to **`ai-box`** at `/var/log/remote/qidi/`.

---

## 🏗️ Architectural Coverage Across All 5 Layers

```
+-----------------------------------------------------------------------------------------+
| Layer 1: QIDI Studio (Slicer)                                                           |
| Payload generation, G-code slicing, profile metadata, layer count & z-height macros    |
+--------------------------------------------+--------------------------------------------+
                                             | Network Upload / REST / WebSockets
                                             v
+-----------------------------------------------------------------------------------------+
| Layer 2: Moonraker (Web API Server on Printer SoC)                                      |
| HTTP upload queue, websocket event stream (ws://192.168.1.27/websocket), job state      |
+--------------------------------------------+--------------------------------------------+
                                             | Unix Socket / JSON-RPC
                                             v
+-----------------------------------------------------------------------------------------+
| Layer 3: Klippy (Klipper Host Python Process)                                           |
| Kinematics, gcode execution, input shaper, PID control, stats loop, klippy.log          |
+--------------------------------------------+--------------------------------------------+
                                             | Serial / USB / CAN Bus
                                             v
+-----------------------------------------------------------------------------------------+
| Layer 4: Microcontroller Units (MCU / Toolhead THR / Box)                               |
| Stepper timing schedules, clock sync, retransmits, mcu_awake %, shutdown tracebacks     |
+--------------------------------------------+--------------------------------------------+
                                             | PWM / Electrical Current / Analog Signals
                                             v
+-----------------------------------------------------------------------------------------+
| Layer 5: Physical Hardware & Sensors                                                    |
| Steppers, extruder & bed thermistors, active chamber heater, ADXL345, bed mesh         |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v  Continuous Stream
                       +-------------------------------------------+
                       |    qidi_streamer.py Daemon on ai-box     |
                       +-------------------------------------------+
                                             |
                                             v  /var/log/remote/qidi/
             +-------------------------------+-------------------------------+
             |                               |                               |
             v                               v                               v
     `qidi.log`                      `events.log`                     `qidi_raw.jsonl`
(Formatted Telemetry &          (Layer changes, job state,        (Raw JSON-RPC frames for
 G-Code Console Output)          warnings, and file uploads)        Agentic Root-Cause Analysis)
```

---

## 🔍 How Each Layer's Data is Captured

1. **Layer 1 (QIDI Studio):**
   * **Capture:** Slicer uploads G-code to Moonraker (`/server/files/upload`). Moonraker emits `notify_filelist_changed` and parses file header metadata (`INFO:metadata:Object Processing is enabled`).
   * **Enrichment (Layer Macro):** In QIDI Studio **Printer Settings -> Custom G-code -> Before Layer Change G-code**, insert:
     ```gcode
     M118 [LAYER_CHANGE] Layer {layer_num}/{total_layer_count} - Height: {layer_z}mm
     ```
     This instructs Klippy to broadcast precise layer transitions over the WebSocket stream in real time.

2. **Layer 2 (Moonraker API):**
   * **Capture:** The daemon connects to `ws://192.168.1.27/websocket` and subscribes to Moonraker system events (`notify_history_changed`, `notify_filelist_changed`, `notify_cpu_throttled`).

3. **Layer 3 (Klippy Host):**
   * **Capture:** Listens to `notify_gcode_response` for `M118` / `RESPOND` output, macro messages, and error tracebacks.
   * **Log Sync:** `klippy.log` stats (emitted every 1 second) are polled or synced to `/var/log/remote/qidi/klippy.log`.

4. **Layer 4 (MCU / Mainboard / Toolhead):**
   * **Capture:** MCU statistics (`mcu_awake`, `bytes_retransmit`, `srtt`, `rto`, sequence counts) are embedded in Klippy status frames and extracted live into `qidi.log`.
   * **Emergency Tracebacks:** MCU shutdown panics (`Timer too close`, `ADC out of range`) are logged directly to the event stream.

5. **Layer 5 (Hardware & Sensors):**
   * **Capture:** Real-time sensor readings (`extruder`, `heater_bed`, `chamber`, `fan`, `toolhead`) are updated continuously in `qidi.log`.

---

## 🚀 Quick Deployment Guide

Run the deployment script on **`ai-box`**:

```bash
chmod +x /home/me/repos/random-stuff/qidi-studio/log-streamer/deploy.sh
/home/me/repos/random-stuff/qidi-studio/log-streamer/deploy.sh
```

### Inspect Output Streams:
* **Formatted Live Stream:** `tail -f /var/log/remote/qidi/qidi.log`
* **Layer & Job Events:** `tail -f /var/log/remote/qidi/events.log`
* **Raw JSONL Stream for AI Agents:** `tail -f /var/log/remote/qidi/qidi_raw.jsonl`
