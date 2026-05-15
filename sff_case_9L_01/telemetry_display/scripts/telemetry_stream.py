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

# ==============================================================================
# --- GLOBAL SYSTEM CONFIGURATION ---
# ==============================================================================

COM_PORT = "COM4"
BAUD_RATE = 115200
POLL_INTERVAL = 3.0  

LHM_JSON_URL = "http://localhost:8085/data.json"
HTTP_TIMEOUT = 2.0

CITY_NAME = "Mississauga"
REGION = "Canada"
TIMEZONE = "America/Toronto"
LATITUDE = 43.5890
LONGITUDE = -79.6441

DIM_DELAY_HRS = 1.0      
WAKE_ADVANCE_HRS = 1.0   
BRIGHTNESS_DAY = 100 # max 255 for 8-bit brightness     
BRIGHTNESS_NIGHT = 10 # originlly 30    

# ==============================================================================
# --- SYSTEM LOGIC ---
# ==============================================================================

cityData = LocationInfo(CITY_NAME, REGION, TIMEZONE, LATITUDE, LONGITUDE)

def getTargetBrightness():
    tz = pytz.timezone(cityData.timezone)
    now = datetime.now(tz)
    try:
        solarData = sun(cityData.observer, date=now.date(), tzinfo=tz)
        dimStart = solarData["sunset"] + timedelta(hours=DIM_DELAY_HRS)
        dimStop = solarData["sunrise"] - timedelta(hours=WAKE_ADVANCE_HRS)
        if dimStop <= now <= dimStart: return BRIGHTNESS_DAY
        else: return BRIGHTNESS_NIGHT
    except Exception:
        return BRIGHTNESS_DAY

def fetchHttpTelemetry(metrics):
    def findSensor(node, hw_type=""):
        hid = str(node.get("HardwareId", ""))
        if hid: hw_type = hid.lower()
            
        name = str(node.get("Text", "")).lower()
        val_str = str(node.get("Value", "")).lower()
        
        if val_str:
            try:
                val = str(int(float(val_str.split()[0].replace(',', '.'))))
                val_int = int(val)
            except Exception:
                val, val_int = None, -1
                
            if val is not None:
                if "°c" in val_str:
                    if "/intelcpu" in hw_type and "cpu package" in name:
                        metrics['cpu_temp'] = val
                    elif "/gpu" in hw_type and "gpu core" in name:
                        metrics['gpu_temp'] = val
                    elif "/nvme" in hw_type or "/ssd" in hw_type or "/hdd" in hw_type:
                        if "temperature" in name or "composite" in name:
                            if val_int > int(metrics['ssd_temp']):
                                metrics['ssd_temp'] = val
                elif "%" in val_str:
                    if "/intelcpu" in hw_type and "cpu total" in name:
                        metrics['cpu_load'] = val
                    elif "/gpu" in hw_type and "gpu core" in name:
                        metrics['gpu_load'] = val
                elif "rpm" in val_str:
                    if val_int > 0 and "/gpu" not in hw_type:
                        metrics['fan_list'].append(val_int)

        for childNode in node.get("Children", []):
            findSensor(childNode, hw_type)

    try:
        req = urllib.request.urlopen(LHM_JSON_URL, timeout=HTTP_TIMEOUT)
        dataMap = json.loads(req.read().decode('utf-8'))
        findSensor(dataMap)
    except Exception as e:
        pass

def main():
    serPort = None
    while serPort is None:
        try:
            # CRITICAL FIX: Instantiate without opening to prevent DTR spike
            serPort = serial.Serial()
            serPort.port = COM_PORT
            serPort.baudrate = BAUD_RATE
            serPort.timeout = 1
            serPort.dtr = False
            serPort.rts = False
            serPort.open() # Safely open with transistors disabled
        except serial.SerialException:
            time.sleep(5.0)

    wmiClient = None
    useHttp = False

    try:
        wmiClient = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    except Exception:
        try:
            wmiClient = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        except Exception:
            useHttp = True

    while True:
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
            except Exception:
                useHttp = True 
        else:
            fetchHttpTelemetry(metrics)

        fList = metrics['fan_list']
        avgFan = str(sum(fList) // len(fList)) if fList else "0"
        tBright = getTargetBrightness()
        
        payloadStr = f"<T:{metrics['cpu_temp']},R:{avgFan},G:{metrics['gpu_temp']},M:{metrics['ssd_temp']},C:{metrics['cpu_load']},L:{metrics['gpu_load']},B:{tBright}>\n"
        
        try:
            serPort.write(payloadStr.encode('utf-8'))
        except Exception:
            serPort.close()
            serPort = None
            while serPort is None:
                try:
                    # Safe instantiation for the reconnection loop
                    serPort = serial.Serial()
                    serPort.port = COM_PORT
                    serPort.baudrate = BAUD_RATE
                    serPort.timeout = 1
                    serPort.dtr = False
                    serPort.rts = False
                    serPort.open()
                except serial.SerialException:
                    time.sleep(5.0)
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()