#!/usr/bin/env python3
"""
QIDI 3D Printer Log & Telemetry Streamer Daemon for ai-box
Connects to Moonraker's live WebSocket endpoint (ws://<printer_ip>/websocket)
and streams formatted + raw telemetry/logs from all QIDI layers to /var/log/remote/qidi/
with auto-reconnection and layer-by-layer tracking.
"""

import asyncio
import json
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
import websockets
import urllib.request

# Configuration defaults
PRINTER_IP = os.environ.get("PRINTER_IP", "192.168.1.27")
LOG_DIR = os.environ.get("LOG_DIR", "/var/log/remote/qidi")
RECONNECT_DELAY = 5  # seconds

WEBSOCKET_URI = f"ws://{PRINTER_IP}/websocket"

# Setup system logger for daemon diagnostics
syslog_handler = logging.handlers.SysLogHandler(address="/dev/log" if os.path.exists("/dev/log") else ("localhost", 514))
syslog_formatter = logging.Formatter("qidi-streamer[%(process)d]: [%(levelname)s] %(message)s")
syslog_handler.setFormatter(syslog_formatter)

logger = logging.getLogger("qidi-streamer")
logger.setLevel(logging.INFO)
logger.addHandler(syslog_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(syslog_formatter)
logger.addHandler(console_handler)


def ensure_log_dir():
    """Ensure the target log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)


def format_gcode_response(msg: str) -> str:
    """Format a Klippy gcode response or layer change broadcast."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{timestamp} [KLIPPY:GCODE] {msg.strip()}\n"


def format_status_update(status_data: dict) -> str:
    """Format live status update (temperatures, print progress, layer info)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = []

    # Print stats
    if "print_stats" in status_data:
        ps = status_data["print_stats"]
        state = ps.get("state")
        filename = ps.get("filename")
        if state:
            parts.append(f"state={state}")
        if filename:
            parts.append(f"file='{filename}'")
        if "info" in ps and ps["info"]:
            cur_l = ps["info"].get("current_layer")
            tot_l = ps["info"].get("total_layer")
            if cur_l is not None and tot_l is not None:
                parts.append(f"layer={cur_l}/{tot_l}")

    # Extruder
    if "extruder" in status_data:
        ext = status_data["extruder"]
        temp = ext.get("temperature")
        target = ext.get("target")
        if temp is not None:
            target_str = f"{target:.1f}°C" if isinstance(target, (int, float)) else "N/A"
            parts.append(f"extruder={temp:.1f}°C(target:{target_str})")

    # Bed
    if "heater_bed" in status_data:
        bed = status_data["heater_bed"]
        temp = bed.get("temperature")
        target = bed.get("target")
        if temp is not None:
            target_str = f"{target:.1f}°C" if isinstance(target, (int, float)) else "N/A"
            parts.append(f"bed={temp:.1f}°C(target:{target_str})")

    # Chamber
    if "chamber" in status_data:
        ch = status_data["chamber"]
        temp = ch.get("temperature")
        target = ch.get("target")
        if temp is not None:
            target_str = f"{target:.1f}°C" if isinstance(target, (int, float)) else "N/A"
            parts.append(f"chamber={temp:.1f}°C(target:{target_str})")

    if parts:
        return f"{timestamp} [PRINTER:TELEMETRY] {' | '.join(parts)}\n"
    return ""


async def stream_moonraker_websocket(qidi_file, events_file, raw_file):
    """Main WebSocket connection and subscription routine."""
    request_id = 1
    while True:
        try:
            logger.info(f"Connecting to Moonraker WebSocket at {WEBSOCKET_URI}...")
            async with websockets.connect(WEBSOCKET_URI, ping_interval=20, ping_timeout=10) as ws:
                logger.info(f"Connected to QIDI printer at {WEBSOCKET_URI}")

                # 1. Subscribe to Klippy objects (Print stats, toolhead, heaters, chamber)
                sub_request = {
                    "jsonrpc": "2.0",
                    "method": "printer.objects.subscribe",
                    "params": {
                        "objects": {
                            "print_stats": None,
                            "webhooks": None,
                            "toolhead": None,
                            "extruder": None,
                            "heater_bed": None,
                            "chamber": None,
                            "fan": None,
                            "gcode_move": None
                        }
                    },
                    "id": request_id
                }
                request_id += 1
                await ws.send(json.dumps(sub_request))

                # 2. Main message loop
                async for message in ws:
                    try:
                        data = json.loads(message)
                        ts = time.time()

                        # Write raw frame for AI Agent RCA parsing
                        raw_entry = json.dumps({"ts": ts, "data": data}) + "\n"
                        raw_file.write(raw_entry)
                        raw_file.flush()

                        method = data.get("method")
                        params = data.get("params", [])

                        # Handle G-Code responses & Console output (Klippy / Layer changes)
                        if method == "notify_gcode_response":
                            for item in params:
                                formatted = format_gcode_response(str(item))
                                qidi_file.write(formatted)
                                qidi_file.flush()
                                if "[LAYER_CHANGE]" in str(item) or "PRINT_" in str(item):
                                    events_file.write(formatted)
                                    events_file.flush()

                        # Handle live status updates (MCU/Printer state/Sensors)
                        elif method == "notify_status_update":
                            if params and isinstance(params, list):
                                status_dict = params[0]
                                formatted = format_status_update(status_dict)
                                if formatted:
                                    qidi_file.write(formatted)
                                    qidi_file.flush()

                        # Handle job history / file upload notifications (QIDI Studio / Moonraker layer)
                        elif method in ["notify_history_changed", "notify_filelist_changed"]:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            event_msg = f"{timestamp} [MOONRAKER:EVENT] {method} -> {params}\n"
                            qidi_file.write(event_msg)
                            events_file.write(event_msg)
                            qidi_file.flush()
                            events_file.flush()

                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON frame received: {message[:100]}")
                    except Exception as err:
                        logger.error(f"Error processing message frame: {err}")

        except asyncio.CancelledError:
            logger.info("WebSocket streamer task cancelled.")
            break
        except Exception as e:
            logger.warning(f"Connection lost to QIDI printer ({e}). Reconnecting in {RECONNECT_DELAY}s...")
            await asyncio.sleep(RECONNECT_DELAY)


async def main():
    ensure_log_dir()

    qidi_log_path = os.path.join(LOG_DIR, "qidi.log")
    events_log_path = os.path.join(LOG_DIR, "events.log")
    raw_log_path = os.path.join(LOG_DIR, "qidi_raw.jsonl")

    logger.info(f"Starting QIDI Log Streamer targeting Printer IP {PRINTER_IP}")
    logger.info(f"Log output directory: {LOG_DIR}")

    with open(qidi_log_path, "a", encoding="utf-8") as q_file, \
         open(events_log_path, "a", encoding="utf-8") as e_file, \
         open(raw_log_path, "a", encoding="utf-8") as r_file:

        task = asyncio.create_task(stream_moonraker_websocket(q_file, e_file, r_file))

        try:
            await task
        except asyncio.CancelledError:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("QIDI Log Streamer stopped by user.")
        sys.exit(0)
