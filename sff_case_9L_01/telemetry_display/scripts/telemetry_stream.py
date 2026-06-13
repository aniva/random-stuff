import time
import serial
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

# --- Solar Offset Logic ---
DIM_OFFSET_HRS = -0.5    # Negative value = 30 mins BEFORE sunset
WAKE_OFFSET_HRS = 0.75   # Positive value = 45 mins AFTER sunrise

BRIGHTNESS_DAY = 30 # max 255 for 8-bit brightness     
BRIGHTNESS_NIGHT = 3 # Lowers active night brightness to the absolute minimum

# ==============================================================================
# --- SYSTEM LOGIC ---
# ==============================================================================

cityData = LocationInfo(CITY_NAME, REGION, TIMEZONE, LATITUDE, LONGITUDE)

def getTargetBrightness():
    tz = pytz.timezone(cityData.timezone)
    now = datetime.now(tz)
    try:
        solarData = sun(cityData.observer, date=now.date(), tzinfo=tz)
        
        # End of day boundary (triggers night mode)
        dimStart = solarData["sunset"] + timedelta(hours=DIM_OFFSET_HRS)
        
        # Start of day boundary (triggers day mode)
        dimStop = solarData["sunrise"] + timedelta(hours=WAKE_OFFSET_HRS)
        
        # If current time is strictly between the wake boundary and dim boundary:
        if dimStop <= now <= dimStart: 
            return BRIGHTNESS_DAY
        else: 
            return BRIGHTNESS_NIGHT
            
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
                        # CRITICAL: Exclude static threshold limits
                        if "warning" not in name and "critical" not in name:
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
        return True
    except Exception as e:
        return False

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
        except Exception:
            time.sleep(5.0)

    while True:
        metrics = {
            'cpu_temp': "0", 'fan_list': [], 'gpu_temp': "0", 
            'ssd_temp': "0", 'cpu_load': "0", 'gpu_load': "0"
        }

        success = fetchHttpTelemetry(metrics)
        status = 0 if success else 1

        fList = metrics['fan_list']
        avgFan = str(sum(fList) // len(fList)) if fList else "0"
        tBright = getTargetBrightness()
        
        payloadStr = f"<T:{metrics['cpu_temp']},R:{avgFan},G:{metrics['gpu_temp']},M:{metrics['ssd_temp']},C:{metrics['cpu_load']},L:{metrics['gpu_load']},B:{tBright},E:{status}>\n"
        
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
                except Exception:
                    time.sleep(5.0)
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()