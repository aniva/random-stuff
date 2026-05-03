import urllib.request
import json
import serial
import time
import sys
import base64
import socket

# --- Configuration ---
COM_PORT = 'COM3'
BAUD_RATE = 115200
POLL_RATE_SEC = 2.0
LHM_URL = "http://localhost:8085/data.json"
LHM_PORT = 8085
authUser = "sffmonitor"
authPass = "sffmonitor"

def check_lhm_server():
    """Verify LHM web server is actually listening before starting."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        if s.connect_ex(('localhost', LHM_PORT)) == 0:
            return True
        return False

def find_sensors(node, metrics):
    if "Text" in node and "Value" in node:
        text = node["Text"]
        value = node["Value"]
        
        # CPU & GPU Temperatures
        if "CPU Package" in text and "°C" in value:
            metrics['temp'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "GPU Core" in text and "°C" in value and "/gpu-nvidia/" in node.get("SensorId", ""):
            metrics['gpu_t'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        
        # Dynamic Fan Averaging Logic
        elif "Fan" in text and "RPM" in value:
            try:
                rpm_val = int(value.replace(',', '').split()[0])
                if rpm_val > 0:
                    metrics['fan_list'].append(rpm_val)
            except ValueError: pass
            
        # Storage Metrics
        elif "Composite Temperature" in text and "°C" in value:
            metrics['nvme'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "Total Activity" in text and "%" in value:
            metrics['disk_a'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
            
        # Load Metrics
        elif "CPU Total" in text and "%" in value:
            metrics['cpu_l'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"
        elif "GPU Core" in text and "%" in value and "/gpu-nvidia/" in node.get("SensorId", ""):
            metrics['gpu_l'] = f"{int(float(value.replace(',', '.').split()[0])):02d}"

    if "Children" in node:
        for child in node["Children"]:
            find_sensors(child, metrics)

def connect_serial():
    """Attempts to open the serial port and returns the object."""
    while True:
        try:
            ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            ser.dtr = True 
            ser.rts = True
            print(f"[+] Serial connection established on {COM_PORT}")
            return ser
        except (serial.SerialException, PermissionError):
            print(f"[-] Waiting for {COM_PORT}... Is the USB unplugged?")
            time.sleep(2)

def main():
    # 1. Pre-Flight Check: LHM Server Status
    print(f"[*] Checking for LHM server on port {LHM_PORT}...")
    while not check_lhm_server():
        print("[-] LHM Web Server not detected. Ensure it is started in LHM options.")
        time.sleep(5)
    print("[+] LHM Server detected.")

    # 2. Establish Serial Link
    ser = connect_serial()
    
    authStr = f"{authUser}:{authPass}"
    authB64 = base64.b64encode(authStr.encode('ascii')).decode('ascii')
    
    print(f"[*] Monitoring LHM at {LHM_URL}...")
    
    while True:
        try:
            # Initialize metrics with defaults and an empty list for fan RPM aggregation
            metrics = {
                'temp': "00", 'gpu_t': "00", 'nvme': "00", 
                'cpu_l': "00", 'gpu_l': "00", 'disk_a': "00", 'fan_list': []
            }
            
            # 1. Fetch Data
            req = urllib.request.Request(LHM_URL)
            req.add_header("Authorization", f"Basic {authB64}")
            try:
                with urllib.request.urlopen(req, timeout=1) as response:
                    data = json.loads(response.read().decode())
                    find_sensors(data, metrics)
            except Exception as e:
                print(f"[-] HTTP Error: {e}")
                time.sleep(POLL_RATE_SEC)
                continue

            # Compute average RPM
            avg_rpm = sum(metrics['fan_list']) // len(metrics['fan_list']) if metrics['fan_list'] else 0

            # 2. Construct & Send Payload
            payload = f"<T:{metrics['temp']},R:{avg_rpm:04d},G:{metrics['gpu_t']},M:{metrics['nvme']},C:{metrics['cpu_l']},L:{metrics['gpu_l']},D:{metrics['disk_a']}>\n"
            
            try:
                ser.write(payload.encode('utf-8'))
                print(f"Tx: {payload.strip()}")
            except (serial.SerialException, serial.PortNotOpenError, Exception) as e:
                print(f"[!] Serial link lost: {e}. Attempting recovery...")
                ser.close()
                ser = connect_serial() 

        except KeyboardInterrupt:
            print("\n[*] Terminating daemon.")
            ser.close()
            sys.exit(0)
        except Exception as e:
            print(f"[-] Data Extraction Error: {e}")
        
        time.sleep(POLL_RATE_SEC)

if __name__ == "__main__":
    main()