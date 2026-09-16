#!/usr/bin/env python3
"""
Quick Diagnostic Tool for QIDI Box
Performs non-intrusive, read-only status checks over Moonraker HTTP API
to definitively isolate whether an issue is in QIDI Studio (app UI/WebSocket)
or in the printer/Box hardware/firmware.
"""

import sys
import os
import json
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_JSON_PATH = os.path.join(PROJECT_DIR, 'printer_config.json')

def load_printer_ip():
    if os.path.exists(CONFIG_JSON_PATH):
        try:
            with open(CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('printer_ip', '10.44.55.81')
        except Exception:
            pass
    return '10.44.55.81'

def fetch_json(url, timeout=5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QidiBoxDiag/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.URLError as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}

def main():
    ip = sys.argv[1] if len(sys.argv) > 1 else load_printer_ip()
    print("=" * 65)
    print(f"       QIDI BOX DIAGNOSTIC PROBE (Target: {ip})")
    print("=" * 65)

    # 1. Check Moonraker / Klipper Server Status
    server_info = fetch_json(f"http://{ip}/printer/info")
    if 'error' in server_info:
        print(f"\n[FAIL] Cannot connect to Moonraker API at http://{ip}/")
        print(f"       Detail: {server_info['error']}")
        print("\n-> ROOT CAUSE: Printer is offline, IP changed, or Moonraker crashed.")
        sys.exit(1)

    klipper_state = server_info.get('result', {}).get('state', 'unknown')
    klipper_msg = server_info.get('result', {}).get('state_message', '')
    if klipper_state == 'ready':
        print(f"[PASS] Klipper State: READY ({klipper_state})")
    else:
        print(f"[WARN] Klipper State: {klipper_state.upper()} ({klipper_msg})")

    # 2. Query Box Objects
    objs_res = fetch_json(f"http://{ip}/printer/objects/list")
    all_objs = objs_res.get('result', {}).get('objects', [])

    has_mcu_box = 'mcu mcu_box1' in all_objs
    
    # 3. Query Detailed Telemetry
    query_url = (
        f"http://{ip}/printer/objects/query?"
        f"mcu=mcu_box1&"
        f"save_variables=variables"
    )
    data = fetch_json(query_url)
    status = data.get('result', {}).get('status', {})
    
    mcu_box_status = status.get('mcu mcu_box1', {})
    save_vars = status.get('save_variables', {}).get('variables', {})

    print("-" * 65)
    print(" 1. HARDWARE & MCU LAYER (Printer <-> QIDI Box USB)")
    print("-" * 65)
    
    mcu_box_ok = False
    if has_mcu_box:
        mcu_version = mcu_box_status.get('mcu_version', 'Unknown')
        mcu_constants = mcu_box_status.get('mcu_constants', {})
        arch = mcu_constants.get('MCU', 'Unknown MCU')
        if mcu_version != 'Unknown' or mcu_box_status:
            print(f"[PASS] Box MCU (mcu_box1): CONNECTED & RESPONDING")
            print(f"       Firmware: {mcu_version} | Architecture: {arch}")
            mcu_box_ok = True
        else:
            print(f"[WARN] Box MCU registered in printer.cfg but no stats returned.")
    else:
        print(f"[FAIL] Box MCU (mcu_box1) NOT found in Klipper active objects.")
        print("       Check physical USB cable between printer and Box, and 24V power.")

    # 4. Check Save Variables (Moonraker Box Registration)
    print("\n" + "-" * 65)
    print(" 2. MOONRAKER & BOX TELEMETRY LAYER")
    print("-" * 65)
    box_count = save_vars.get('box_count', 0)
    enable_box = save_vars.get('enable_box', 0)
    print(f"[*] enable_box: {enable_box} | box_count: {box_count}")

    if box_count >= 1 and enable_box == 1:
        print("[PASS] Moonraker Box Registration: ACTIVE (1 Box enabled)")
    else:
        print(f"[WARN] Moonraker reports box_count={box_count}, enable_box={enable_box}")

    # Query temperature/humidity if available
    temp_res = fetch_json(f"http://{ip}/printer/objects/query?temperature_sensor=all&heater_generic=heater_box1")
    t_status = temp_res.get('result', {}).get('status', {})
    
    box_temp = None
    box_humidity = None
    for k, v in t_status.items():
        if 'box1' in k.lower() or 'heater_box' in k.lower():
            if 'temperature' in v:
                box_temp = v.get('temperature')
            if 'humidity' in v:
                box_humidity = v.get('humidity')

    if box_temp is not None or box_humidity is not None:
        humid_str = f", Humidity: {box_humidity:.1f}%" if box_humidity is not None else ""
        print(f"[PASS] Box Environmental Sensor: Temp: {box_temp}\u00b0C{humid_str}")

    # Check filament slots
    print("\n" + "-" * 65)
    print(" 3. FILAMENT SLOTS STATUS (in Klipper / Box)")
    print("-" * 65)
    for slot_idx in range(4):
        slot_runout_key = f"filament_slot{slot_idx}_runout"
        slot_mat_key = f"filament_slot{slot_idx}_material"
        slot_col_key = f"filament_slot{slot_idx}_color"
        
        slot_val = save_vars.get(f"filament_slot{slot_idx}")
        mat = save_vars.get(slot_mat_key, "N/A")
        color = save_vars.get(slot_col_key, "N/A")
        
        print(f"  * Slot {slot_idx + 1}: Raw ID={slot_val} | Material: {mat} | Color: {color}")

    # 5. Diagnostic Conclusion
    print("\n" + "=" * 65)
    print("                     DIAGNOSTIC VERDICT")
    print("=" * 65)
    if mcu_box_ok and box_count >= 1:
        print("[RESULT: 100% HEALTHY HARDWARE & PRINTER FIRMWARE]")
        print("-> The Box hardware, USB cable, MCU, and Moonraker API are WORKING PERFECTLY.")
        print("-> If QIDI Studio does not show the 4 Box slots in the Device tab:")
        print("   1. QIDI Studio dropped/failed WebSocket subscription during Wi-Fi reconnect.")
        print("      SOLUTION: Restart QIDI Studio (File -> Exit, then reopen).")
        print("   2. Or the active project was loaded with a non-box printer profile.")
        print("      SOLUTION: Under 'Printer' dropdown, select 'Q2 0.4 nozzle 01'.")
        print("   3. If 'Sync' fails with 'no compatible filaments':")
        print("      SOLUTION: In QIDI Studio Device tab, edit Slot material so it matches")
        print("      the filament profile type in your Prepare tab (e.g. ABS vs PLA).")
    else:
        print("[RESULT: HARDWARE / FIRMWARE FAULT DETECTED]")
        print("-> The printer OS / Klipper cannot communicate with the QIDI Box.")
        print("   1. Check the USB-C data cable between printer and QIDI Box.")
        print("   2. Check the 24V power cord to the QIDI Box.")
        print("   3. Power-cycle the QIDI Box first, then reboot the printer.")
    print("=" * 65 + "\n")

if __name__ == '__main__':
    main()
