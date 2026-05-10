import time
import serial
import wmi
import sys
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz

# --- Dimming Configuration ---
cityData = LocationInfo("Mississauga", "Canada", "America/Toronto", 43.5890, -79.6441)
xOffsetHrs = 1.0  # Hours AFTER sunset to start dimming
yOffsetHrs = 1.0  # Hours BEFORE sunrise to stop dimming
brightnessDay = 255
brightnessNight = 30

def getTargetBrightness():
    tz = pytz.timezone(cityData.timezone)
    now = datetime.now(tz)
    try:
        solarData = sun(cityData.observer, date=now.date(), tzinfo=tz)
        dimStart = solarData["sunset"] + timedelta(hours=xOffsetHrs)
        dimStop = solarData["sunrise"] - timedelta(hours=yOffsetHrs)
        
        if dimStop <= now <= dimStart:
            return brightnessDay
        else:
            return brightnessNight
    except Exception as e:
        print(f"[-] Solar calculation error: {e}")
        return brightnessDay

def fetchHttpTelemetry():
    def findSensor(node, tempRef, rpmRef):
        textData = node.get("Text", "")
        valueStr = node.get("Value", "")
        
        if "CPU Package" in textData and "°C" in valueStr:
            try:
                tempRef[0] = str(int(float(valueStr.split(" ")[0].replace(',', '.'))))
            except ValueError:
                pass
                
        if "RPM" in valueStr:
            if "CPU" in textData or rpmRef[0] == "0":
                try:
                    rpmRef[0] = str(int(float(valueStr.split(" ")[0].replace(',', '.'))))
                except ValueError:
                    pass
                
        for childNode in node.get("Children", []):
            findSensor(childNode, tempRef, rpmRef)

    try:
        req = urllib.request.urlopen("http://localhost:8085/data.json", timeout=2)
        dataMap = json.loads(req.read().decode('utf-8'))
        tRef = ["0"]
        rRef = ["0"]
        findSensor(dataMap, tRef, rRef)
        return tRef[0], rRef[0]
    except Exception:
        return "0", "0"

def main():
    comPort = "COM3"
    baudRate = 115200 
    
    try:
        serPort = serial.Serial(comPort, baudRate, timeout=1)
    except serial.SerialException as e:
        print(f"Error: Could not open {comPort}. {e}")
        sys.exit(1)

    print("Connecting to WMI (LibreHardwareMonitor)...")
    wmiClient = None
    useHttp = False

    try:
        wmiClient = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    except wmi.x_wmi as e:
        print(f"[Debug] LHM Namespace Error: {e}")
        try:
            wmiClient = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        except wmi.x_wmi as e2:
            print(f"[Debug] OHM Namespace Error: {e2}")
            print("\n[Fallback] Failed to connect to WMI.")
            print("Switching to HTTP Web Server fallback mode...")
            useHttp = True

    print(f"Streaming telemetry payload to {comPort}... (Press Ctrl+C to stop)")

    while True:
        cpuTemp = "0"
        fanRpm = "0"

        if not useHttp:
            try:
                for sensorObj in wmiClient.Sensor():
                    if sensorObj.SensorType == "Temperature" and "CPU Package" in sensorObj.Name:
                        cpuTemp = str(int(sensorObj.Value))
                    elif sensorObj.SensorType == "Fan" and "CPU" in sensorObj.Name:
                        fanRpm = str(int(sensorObj.Value))
            except Exception as e:
                print(f"WMI Error: {e}")
        else:
            cpuTemp, fanRpm = fetchHttpTelemetry()

        targetBrightness = getTargetBrightness()
        payloadStr = f"<T:{cpuTemp},R:{fanRpm},B:{targetBrightness}>\n"
        
        try:
            serPort.write(payloadStr.encode('utf-8'))
            print(f"Transmitted: {payloadStr.strip()}")
        except Exception as e:
            print(f"Serial Error: {e}")
        
        time.sleep(2.0)

if __name__ == "__main__":
    main()