import time
import serial
import wmi
import urllib.request
import json

def get_web_telemetry():
    try:
        req = urllib.request.urlopen("http://localhost:8085/data.json", timeout=1)
        data = json.loads(req.read())
        
        cpu_temp = 0
        fan_rpm = 0
        
        def search_node(node):
            nonlocal cpu_temp, fan_rpm
            text = node.get("Text", "")
            val = node.get("Value", "")
            
            if ("CPU Package" in text or "CPU Core" in text) and "°C" in val:
                try:
                    cpu_temp = int(float(val.replace(" °C", "").replace("°C", "").replace(",", ".").strip()))
                except ValueError:
                    pass
            elif ("Fan #1" in text or "CPU Fan" in text) and "RPM" in val:
                try:
                    fan_rpm = int(float(val.replace(" RPM", "").replace("RPM", "").replace(",", ".").strip()))
                except ValueError:
                    pass
                    
            for child in node.get("Children", []):
                search_node(child)
        
        search_node(data)
        return cpu_temp, fan_rpm
    except Exception:
        return None, None

def main():
    PORT = 'COM3'
    BAUD = 115200

    print("Connecting to WMI (LibreHardwareMonitor)...")
    w = None
    
    # Try LibreHardwareMonitor's native namespace first
    try:
        w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    except Exception as e1:
        print(f"[Debug] LHM Namespace Error: {e1}")
        # Fallback to legacy OpenHardwareMonitor namespace
        try:
            w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        except Exception as e2:
            print(f"[Debug] OHM Namespace Error: {e2}")

    use_web_api = False
    if w is None:
        print("\n[Fallback] Failed to connect to WMI.")
        print("Switching to HTTP Web Server fallback mode...")
        print("Please ensure LibreHardwareMonitor has 'Options -> Run Web Server' checked (Port 8085).\n")
        use_web_api = True

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"Failed to open {PORT}. Ensure it is not locked by the PlatformIO Serial Monitor.")
        return

    print(f"Streaming telemetry payload to {PORT}... (Press Ctrl+C to stop)")

    try:
        while True:
            cpu_temp = 0
            fan_rpm = 0

            if not use_web_api:
                # Iterate through WMI sensors to find the target data
                sensors = w.Sensor()
                for sensor in sensors:
                    # Note: You may need to tweak the sensor.Name conditions to perfectly match your hardware
                    if sensor.SensorType == 'Temperature' and ('CPU Package' in sensor.Name or 'CPU Core' in sensor.Name):
                        cpu_temp = int(sensor.Value)
                    elif sensor.SensorType == 'Fan' and ('Fan #1' in sensor.Name or 'CPU Fan' in sensor.Name):
                        fan_rpm = int(sensor.Value)
            else:
                t, r = get_web_telemetry()
                if t is not None and r is not None:
                    cpu_temp = t
                    fan_rpm = r
                else:
                    print("[Warn] Failed to read from Web Server. Is 'Options -> Run Web Server' checked?")

            payload = f"<T:{cpu_temp},R:{fan_rpm}>"
            ser.write(payload.encode('ascii'))
            print(f"Transmitted: {payload}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping telemetry stream...")
    finally:
        ser.close()

if __name__ == '__main__':
    main()