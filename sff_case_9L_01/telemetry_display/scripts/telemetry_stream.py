import urllib.request
import json
import serial
import time
import sys

# --- Configuration ---
COM_PORT = 'COM3'
BAUD_RATE = 115200
POLL_RATE_SEC = 2.0
LHM_URL = "http://localhost:8085/data.json"

def find_sensors(node, metrics):
    """Recursively traverse the LHM JSON tree to extract values."""
    if "Text" in node and "Value" in node:
        text = node["Text"]
        value = node["Value"]

        # 1. Match CPU Package Temperature
        if "CPU Package" in text and "°C" in value:
            try:
                # Isolate the float, convert to int, pad to 2 digits
                num = float(value.replace(",", ".").split()[0])
                metrics['temp'] = f"{int(num):02d}"
            except ValueError: pass
        
        # 2. Match Fan RPM
        elif "Fan" in text and "RPM" in value:
            try:
                # Isolate the integer, capture the first non-zero fan found
                num = int(value.replace(",", "").split()[0])
                if num > 0 and metrics['rpm'] == "0000":
                    metrics['rpm'] = f"{num:04d}"
            except ValueError: pass

    # Recurse through hardware children
    if "Children" in node:
        for child in node["Children"]:
            find_sensors(child, metrics)

def main():
    # 1. Initialize Serial Connection
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        ser.dtr = True # Mandatory for ESP32-C6 Native USB
        ser.rts = True
        print(f"[+] Serial connection established on {COM_PORT}")
    except serial.SerialException as e:
        print(f"[-] FATAL: Could not open {COM_PORT}. {e}")
        sys.exit(1)

    print(f"[*] Connecting to LHM Web Server at {LHM_URL}...")
    
    # 2. Main Telemetry Loop
    while True:
        try:
            metrics = {'temp': "00", 'rpm': "0000"}
            
            # Request JSON payload from localhost
            req = urllib.request.Request(LHM_URL)
            with urllib.request.urlopen(req, timeout=1) as response:
                data = json.loads(response.read().decode())
                find_sensors(data, metrics)

            # Construct Payload: <T:XX,R:XXXX>
            payload = f"<T:{metrics['temp']},R:{metrics['rpm']}>\n"
            ser.write(payload.encode('utf-8'))
            print(f"Tx: {payload.strip()}")

        except KeyboardInterrupt:
            print("\n[*] Terminating daemon.")
            ser.close()
            sys.exit(0)
        except Exception as e:
            print(f"[-] Data Extraction Error: {e}")
        
        time.sleep(POLL_RATE_SEC)

if __name__ == "__main__":
    main()