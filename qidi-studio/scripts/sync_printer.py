#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.error
import uuid

# Base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_JSON_PATH = os.path.join(PROJECT_DIR, 'printer_config.json')
LOCAL_CONFIG_DIR = os.path.join(PROJECT_DIR, 'printer_config')

def load_printer_ip():
    if not os.path.exists(CONFIG_JSON_PATH):
        print(f"Error: {CONFIG_JSON_PATH} not found. Please create it.")
        sys.exit(1)
    try:
        with open(CONFIG_JSON_PATH, 'r') as f:
            data = json.load(f)
            ip = data.get('printer_ip')
            if not ip or ip == "192.168.1.100":
                print("Error: Please update 'printer_ip' in printer_config.json with your actual printer IP.")
                sys.exit(1)
            return ip
    except Exception as e:
        print(f"Error parsing {CONFIG_JSON_PATH}: {e}")
        sys.exit(1)

def http_get(ip, path):
    url = f"http://{ip}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read()
    except urllib.error.URLError as e:
        print(f"HTTP GET failed to {url}: {e}")
        sys.exit(1)

def http_post(ip, path, data=None, headers=None):
    url = f"http://{ip}{path}"
    req = urllib.request.Request(url, data=data, headers=headers or {}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except urllib.error.URLError as e:
        print(f"HTTP POST failed to {url}: {e}")
        sys.exit(1)

def parse_includes(content_str):
    includes = []
    for line in content_str.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';'):
            continue
        # Match [include filename.cfg]
        match = re.match(r'\[include\s+([^\]]+)\]', line)
        if match:
            includes.append(match.group(1).strip())
    return includes

def pull_configs(ip):
    print(f"Connecting to printer at {ip} to pull configurations...")
    os.makedirs(LOCAL_CONFIG_DIR, exist_ok=True)
    
    # 1. Download printer.cfg
    print("Downloading printer.cfg...")
    printer_cfg_bytes = http_get(ip, "/server/files/config/printer.cfg")
    printer_cfg_str = printer_cfg_bytes.decode('utf-8', errors='ignore')
    
    with open(os.path.join(LOCAL_CONFIG_DIR, 'printer.cfg'), 'wb') as f:
        f.write(printer_cfg_bytes)
    
    # 2. Parse includes
    includes = parse_includes(printer_cfg_str)
    print(f"Found {len(includes)} included files to download: {includes}")
    
    # 3. Download included files
    for include in includes:
        local_path = os.path.join(LOCAL_CONFIG_DIR, include)
        local_subdir = os.path.dirname(local_path)
        if local_subdir:
            os.makedirs(local_subdir, exist_ok=True)
            
        print(f"Downloading {include}...")
        try:
            include_bytes = http_get(ip, f"/server/files/config/{include}")
            with open(local_path, 'wb') as f:
                f.write(include_bytes)
        except Exception as e:
            print(f"Warning: Failed to download {include}: {e}")
            
    print(f"Pull completed successfully! Files saved to: {LOCAL_CONFIG_DIR}")

def upload_file(ip, relative_path, file_bytes):
    boundary = uuid.uuid4().hex
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    
    # Construct multipart body for Moonraker file upload API
    filename = relative_path.replace(os.sep, '/')
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode('utf-8') + file_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    return http_post(ip, "/server/files/upload?root=config", data=body, headers=headers)

def push_configs(ip):
    if not os.path.exists(LOCAL_CONFIG_DIR):
        print(f"Error: Local configuration directory {LOCAL_CONFIG_DIR} does not exist. Run pull first.")
        sys.exit(1)
        
    print(f"Scanning {LOCAL_CONFIG_DIR} for configuration files to upload...")
    files_to_upload = []
    for root, dirs, files in os.walk(LOCAL_CONFIG_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, LOCAL_CONFIG_DIR)
            files_to_upload.append((full_path, rel_path))
            
    if not files_to_upload:
        print("No files found to upload.")
        return
        
    print(f"Uploading {len(files_to_upload)} files to printer config root...")
    for full_path, rel_path in files_to_upload:
        print(f"Uploading {rel_path}...")
        with open(full_path, 'rb') as f:
            content = f.read()
        upload_file(ip, rel_path, content)
        
    print("Upload completed successfully!")
    restart_klipper(ip)

def restart_klipper(ip):
    print("Triggering Klipper service restart...")
    res = http_post(ip, "/server/restart")
    print(f"Klipper restart response: {res.decode('utf-8')}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print("Usage: python sync_printer.py [pull | push | restart]")
        print("Commands:")
        print("  pull     Download printer.cfg and all included configs from the printer")
        print("  push     Upload local printer_config/ files to the printer and restart Klipper")
        print("  restart  Trigger Klipper restart on the printer")
        sys.exit(0)
        
    cmd = sys.argv[1].lower()
    ip = load_printer_ip()
    
    if cmd == 'pull':
        pull_configs(ip)
    elif cmd == 'push':
        push_configs(ip)
    elif cmd == 'restart':
        restart_klipper(ip)
    else:
        print(f"Error: Unknown command '{cmd}'")
        print("Usage: python sync_printer.py [pull | push | restart]")
        sys.exit(1)

if __name__ == '__main__':
    main()
