import time
import serial
import wmi

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

    if w is None:
        print("Failed to connect to WMI.")
        print("1. Ensure LibreHardwareMonitor is running as ADMINISTRATOR.")
        print("2. Ensure WMI Server is enabled in LibreHardwareMonitor (Options -> Run WMI Server).")
        return

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

            # Iterate through WMI sensors to find the target data
            sensors = w.Sensor()
            for sensor in sensors:
                # Note: You may need to tweak the sensor.Name conditions to perfectly match your hardware
                if sensor.SensorType == 'Temperature' and ('CPU Package' in sensor.Name or 'CPU Core' in sensor.Name):
                    cpu_temp = int(sensor.Value)
                elif sensor.SensorType == 'Fan' and ('Fan #1' in sensor.Name or 'CPU Fan' in sensor.Name):
                    fan_rpm = int(sensor.Value)

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