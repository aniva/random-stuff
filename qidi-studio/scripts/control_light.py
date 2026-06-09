#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

# Base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_JSON_PATH = os.path.join(PROJECT_DIR, 'printer_config.json')

def load_printer_ip():
    if not os.path.exists(CONFIG_JSON_PATH):
        print(f"Error: {CONFIG_JSON_PATH} not found. Please create it.")
        sys.exit(1)
    try:
        with open(CONFIG_JSON_PATH, 'r') as f:
            data = json.load(f)
            ip = data.get('printer_ip')
            if not ip or ip == "192.168.1.100":
                print("Error: Please update 'printer_ip' in printer_config.json with your actual printer IP.")
                sys.exit(1)
            return ip
    except Exception as e:
        print(f"Error parsing {CONFIG_JSON_PATH}: {e}")
        sys.exit(1)

def set_light(ip, state):
    gcode = "LED_ON" if state == "on" else "LED_OFF"
    url = f"http://{ip}/printer/gcode/script"
    
    # URL encoded data: script=LED_ON or script=LED_OFF
    data = urllib.parse.urlencode({"script": gcode}).encode('utf-8')
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        print(f"Sending command '{gcode}' to printer at {ip}...")
        with urllib.request.urlopen(req, timeout=10) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            if resp_data.get("result") == "ok":
                print(f"Chamber light turned {state.upper()} successfully!")
            else:
                print(f"Unexpected response from printer: {resp_data}")
    except urllib.error.URLError as e:
        print(f"Failed to connect to printer at {url}: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        state = "on"
    else:
        state = sys.argv[1].lower()
        
    if state not in ["on", "off"]:
        print("Usage: python control_light.py [on|off]")
        sys.exit(1)
        
    ip = load_printer_ip()
    set_light(ip, state)

if __name__ == "__main__":
    main()
