# Hubitat Integration for AI Agents

This document outlines the standard methods for exposing a Hubitat Elevation Hub to agentic AI workflows (such as coding assistants, automation scripts, or local agents).

---

## Method 1: Maker API (Recommended)
The Maker API is the officially supported, most reliable, and secure method to expose Hubitat devices locally or via cloud relay.

### 1. Setup in Hubitat UI
1. Navigate to **Apps** > **Add Built-In App**.
2. Select **Maker API**.
3. Under the Maker API settings:
   * Select the devices you want to authorize.
   * Enable **Allow Access via Local IP Address**.
   * Note the **App ID** (from the URLs, e.g., `/apps/api/89/...` where `89` is the App ID).
   * Note the **Access Token** generated at the bottom.

### 2. URL Command Structure

#### Get All Devices (to map names to IDs)
```http
GET http://<hub_ip>/apps/api/<app_id>/devices?access_token=<access_token>
```

#### Get Specific Device State
```http
GET http://<hub_ip>/apps/api/<app_id>/devices/<device_id>?access_token=<access_token>
```

#### Send Command to Device
```http
GET http://<hub_ip>/apps/api/<app_id>/devices/<device_id>/<command>?access_token=<access_token>
```
* **Common commands:** `on`, `off`, `toggle` (if supported by driver), `setLevel/<value>`.

---

## Method 2: Local HTTP/REST Bridge (Fast Translation)
If you want to allow agents to control Hubitat using simple, human-readable commands (e.g., `/toggle/QIDI`), you can run a lightweight Python/Node.js web server on your local machine that maps these aliases to the Maker API URLs.

### Python Flask Bridge Example
```python
import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

HUB_IP = "192.168.1.9"
APP_ID = "YOUR_APP_ID"
TOKEN = "YOUR_ACCESS_TOKEN"

# Map friendly names to Hubitat Device IDs
DEVICE_MAP = {
    "qidi": "1382",
    # Add other devices here
}

@app.route("/control/<device_name>/<command>", methods=["POST", "GET"])
def control_device(device_name, command):
    device_id = DEVICE_MAP.get(device_name.lower())
    if not device_id:
        return jsonify({"error": f"Device {device_name} not found"}), 404
        
    url = f"http://{HUB_IP}/apps/api/{APP_ID}/devices/{device_id}/{command}"
    params = {"access_token": TOKEN}
    
    try:
        response = requests.get(url, params=params)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## Method 3: Event Stream (Real-Time Monitoring)
To feed Hubitat state changes back to an agent in real time:
1. Hubitat exposes an Event Socket at `ws://<hub_ip>/eventsocket`.
2. Any WebSocket client can connect to this endpoint to receive a continuous JSON stream of device events (state changes, button presses, etc.).
