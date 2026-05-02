import time
import serial
import wmi
import sys
import urllib.request
import urllib.error
import json

def fetch_http_telemetry():
    # Recursive function to parse LHM's nested JSON structure
    def find_sensor(node, temp_ref, rpm_ref):
        text = node.get("Text", "")
        value_str = node.get("Value", "")
        
        # Extract CPU Package Temperature
        if "CPU Package" in text and "°C" in value_str:
            try:
                # Extract numeric value, e.g., "45.0 °C" -> "45"
                temp_ref[0] = str(int(float(value_str.split(" ")[0].replace(',', '.'))))
            except ValueError:
                pass
                
        # Extract CPU Fan RPM (Prefer explicit 'CPU' label, otherwise grab first fan)
        if "RPM" in value_str:
            if "CPU" in text or rpm_ref[0] == "0":
                try:
                    rpm_ref[0] = str(int(float(value_str.split(" ")[0].replace(',', '.'))))
                except ValueError:
                    pass
                
        for child in node.get("Children", []):
            find_sensor(child, temp_ref, rpm_ref)

    req = urllib.request.urlopen("http://localhost:8085/data.json", timeout=2)
    data = json.loads(req.read().decode('utf-8'))
    t_ref = ["0"]; r_ref = ["0"]
    find_sensor(data, t_ref, r_ref)
    return t_ref[0], r_ref[0]

def main():
    com_port = "COM3"
    baud_rate = 115200 # Standard baud rate for ESP32 CDC
    
    try:
        # Initialize serial connection
        ser = serial.Serial(com_port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Error: Could not open {com_port}. {e}")
        sys.exit(1)

    print("Connecting to WMI (LibreHardwareMonitor)...")
    w = None
    use_http = False

    try:
        w = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
    except wmi.x_wmi as e:
        print(f"[Debug] LHM Namespace Error: {e}")
        try:
            w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        except wmi.x_wmi as e2:
            print(f"[Debug] OHM Namespace Error: {e2}")
            print("\n[Fallback] Failed to connect to WMI.")
            print("Switching to HTTP Web Server fallback mode...")
            print("Please ensure LibreHardwareMonitor has 'Options -> Run Web Server' checked (Port 8085).\n")
            use_http = True

    print(f"Streaming telemetry payload to {com_port}... (Press Ctrl+C to stop)")

    while True:
        cpu_temp = "0"
        fan_rpm = "0"

        if not use_http:
            try:
                for sensor in w.Sensor():
                    if sensor.SensorType == "Temperature" and "CPU Package" in sensor.Name:
                        cpu_temp = str(int(sensor.Value))
                    elif sensor.SensorType == "Fan" and "CPU" in sensor.Name:
                        fan_rpm = str(int(sensor.Value))
            except Exception as e:
                print(f"WMI Error: {e}")
        else:
            try:
                cpu_temp, fan_rpm = fetch_http_telemetry()
            except Exception as e:
                print("[Warn] Failed to read from Web Server. Is 'Options -> Run Web Server' checked?")
                cpu_temp, fan_rpm = "0", "0"

        payload = f"<T:{cpu_temp},R:{fan_rpm}>\n"
        
        try:
            ser.write(payload.encode('utf-8'))
            print(f"Transmitted: {payload.strip()}")
        except Exception as e:
            print(f"Serial Error: {e}")
        
        time.sleep(2.0)

if __name__ == "__main__":
    main()