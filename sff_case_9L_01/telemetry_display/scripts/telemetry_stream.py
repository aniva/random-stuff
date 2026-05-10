import time
import serial
import wmi
import sys
import urllib.request
import json
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz

# --- Dimming Configuration ---
cityData = LocationInfo("Mississauga", "Canada", "America/Toronto", 43.5890, -79.6441)
xOffsetHrs = 1.0  
yOffsetHrs = 1.0  
brightnessDay = 255
brightnessNight = 30

def getTargetBrightness():
    tz = pytz.timezone(cityData.timezone)
    now = datetime.now(tz)
    try:
        solarData = sun(cityData.observer, date=now.date(), tzinfo=tz)
        dimStart = solarData["sunset"] + timedelta(hours=xOffsetHrs)
        dimStop = solarData["sunrise"] - timedelta(hours=yOffsetHrs)
        if dimStop <= now <= dimStart: return brightnessDay
        else: return brightnessNight
    except Exception:
        return brightnessDay

def fetchHttpTelemetry(metrics):
    def findSensor(node, hw_type=""):
        # Cascade HardwareId down the nested JSON tree
        hid = str(node.get("HardwareId", ""))
        if hid: 
            hw_type = hid.lower()
            
        name = str(node.get("Text", "")).lower()
        val_str = str(node.get("Value", "")).lower()
        
        if val_str:
            try:
                # Strip non-numeric characters and handle comma decimals
                val = str(int(float(val_str.split()[0].replace(',', '.'))))
                val_int = int(val)
            except Exception:
                val, val_int = None, -1
                
            if val is not None:
                # --- TEMPERATURES ---
                if "°c" in val_str:
                    if "/intelcpu" in hw_type and "cpu package" in name:
                        metrics['cpu_temp'] = val
                    elif "/gpu" in hw_type and "gpu core" in name:
                        metrics['gpu_temp'] = val
                    elif "/nvme" in hw_type or "/ssd" in hw_type or "/hdd" in hw_type:
                        if "temperature" in name or "composite" in name:
                            # Keep highest drive temperature
                            if val_int > int(metrics['ssd_temp']):
                                metrics['ssd_temp'] = val
                                
                # --- LOADS ---
                elif "%" in val_str:
                    if "/intelcpu" in hw_type and "cpu total" in name:
                        metrics['cpu_load'] = val
                    elif "/gpu" in hw_type and "gpu core" in name:
                        metrics['gpu_load'] = val
                        
                # --- FANS ---
                elif "rpm" in val_str:
                    # Ignore 0 RPM and exclude GPU fans from chassis average
                    if val_int > 0 and "/gpu" not in hw_type:
                        metrics['fan_list'].append(val_int)

        for childNode in node.get("Children", []):
            findSensor(childNode, hw_type)

    try:
        req = urllib.request.urlopen("http://localhost:8085/data.json", timeout=2)
        dataMap = json.loads(req.read().decode('utf-8'))
        findSensor(dataMap)
    except Exception as e:
        print(f"[!] HTTP Fetch Error: {e}")

def main():
    comPort = "COM3"
    baudRate = 115200 
    try:
        serPort = serial.Serial(comPort, baudRate, timeout=1)
        # Required for Waveshare ESP32-C6 initialization
        serPort.dtr = True
        serPort.rts = True
    except serial.SerialException as e:
        print(f"[-] Error: Could not open {comPort}. {e}")
        sys.exit(1)

    print("[+] Connecting to LibreHardwareMonitor...")
    wmiClient = None
    useHttp = False

    try:
        wmiClient = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    except Exception:
        try:
            wmiClient = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        except Exception:
            useHttp = True
            print("[!] WMI Failed. Utilizing HTTP Web Server fallback.")

    while True:
        # Initialize default metrics dictionary
        metrics = {
            'cpu_temp': "0", 'fan_list': [], 'gpu_temp': "0", 
            'ssd_temp': "0", 'cpu_load': "0", 'gpu_load': "0"
        }

        if not useHttp and wmiClient:
            try:
                for sensorObj in wmiClient.Sensor():
                    if sensorObj.Value is None: continue
                    
                    sName = str(sensorObj.Name).lower()
                    sType = str(sensorObj.SensorType).lower()
                    identifier = str(getattr(sensorObj, 'Identifier', '')).lower()
                    
                    try:
                        val_int = int(float(sensorObj.Value))
                        val = str(val_int)
                    except Exception:
                        continue

                    if sType == "temperature":
                        if "/intelcpu" in identifier and "cpu package" in sName:
                            metrics['cpu_temp'] = val
                        elif "/gpu" in identifier and "gpu core" in sName:
                            metrics['gpu_temp'] = val
                        elif "/nvme" in identifier or "/ssd" in identifier or "/hdd" in identifier:
                            if "temperature" in sName or "composite" in sName:
                                if val_int > int(metrics['ssd_temp']):
                                    metrics['ssd_temp'] = val
                                    
                    elif sType == "load":
                        if "/intelcpu" in identifier and "cpu total" in sName:
                            metrics['cpu_load'] = val
                        elif "/gpu" in identifier and "gpu core" in sName:
                            metrics['gpu_load'] = val
                            
                    elif sType == "fan":
                        if val_int > 0 and "/gpu" not in identifier:
                            metrics['fan_list'].append(val_int)
            except Exception as e:
                print(f"[-] WMI Iteration Error: {e}")
                useHttp = True # Fallback if WMI crashes mid-execution
        else:
            fetchHttpTelemetry(metrics)

        # Process mathematical average of valid fans
        fList = metrics['fan_list']
        avgFan = str(sum(fList) // len(fList)) if fList else "0"

        # Construct and transmit serial payload
        tBright = getTargetBrightness()
        payloadStr = f"<T:{metrics['cpu_temp']},R:{avgFan},G:{metrics['gpu_temp']},M:{metrics['ssd_temp']},C:{metrics['cpu_load']},L:{metrics['gpu_load']},B:{tBright}>\n"
        
        try:
            serPort.write(payloadStr.encode('utf-8'))
            print(f"Transmitted: {payloadStr.strip()}")
        except Exception as e:
            print(f"[-] Serial Transmission Error: {e}")
        
        time.sleep(2.0)

if __name__ == "__main__":
    main()