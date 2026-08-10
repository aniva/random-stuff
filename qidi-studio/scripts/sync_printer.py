#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.error
import uuid
import fnmatch

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
    # Standardize path formatting (must use forward slashes for URLs)
    path = path.replace('\\', '/')
    url = f"http://{ip}{path}"
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            return response.read()
    except urllib.error.URLError as e:
        print(f"HTTP GET failed to {url}: {e}")
        sys.exit(1)

def http_post(ip, path, data=None, headers=None):
    path = path.replace('\\', '/')
    url = f"http://{ip}{path}"
    req = urllib.request.Request(url, data=data, headers=headers or {}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
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

def get_config_files_list(ip):
    res = http_get(ip, "/server/files/list?root=config")
    try:
        data = json.loads(res.decode('utf-8'))
        return [item['path'] for item in data.get('result', [])]
    except Exception as e:
        print(f"Error parsing file list from Moonraker: {e}")
        sys.exit(1)

def pull_configs(ip):
    print(f"Connecting to printer at {ip} to pull configurations...")
    os.makedirs(LOCAL_CONFIG_DIR, exist_ok=True)
    
    # Get all files available on the printer's config folder
    all_printer_files = get_config_files_list(ip)
    
    to_download = {"printer.cfg"}
    downloaded = set()
    
    while to_download:
        current = to_download.pop()
        downloaded.add(current)
        
        # Standardize local file path separator for operating systems
        local_path = os.path.join(LOCAL_CONFIG_DIR, current.replace('/', os.sep))
        local_subdir = os.path.dirname(local_path)
        if local_subdir:
            os.makedirs(local_subdir, exist_ok=True)
            
        print(f"Downloading {current}...")
        try:
            file_bytes = http_get(ip, f"/server/files/config/{current}")
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
                
            # Parse includes to discover recursive dependencies
            content_str = file_bytes.decode('utf-8', errors='ignore')
            includes = parse_includes(content_str)
            for include in includes:
                # Match include pattern against all printer files
                matched = False
                for p_file in all_printer_files:
                    if fnmatch.fnmatchcase(p_file, include):
                        matched = True
                        if p_file not in downloaded:
                            to_download.add(p_file)
                if not matched:
                    # If it wasn't a glob pattern and didn't match anything in list, we add it directly
                    if '*' not in include and '?' not in include:
                        if include not in downloaded:
                            to_download.add(include)
        except Exception as e:
            print(f"Warning: Failed to process {current}: {e}")
            
    print(f"Pull completed successfully! Files saved to: {LOCAL_CONFIG_DIR}")

def upload_file(ip, relative_path, file_bytes):
    boundary = uuid.uuid4().hex
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    
    # Split the relative path into directory path and filename
    # e.g., 'klipper-macros-qd/KAMP_Settings.cfg' -> ('klipper-macros-qd', 'KAMP_Settings.cfg')
    relative_path = relative_path.replace('\\', '/')
    if '/' in relative_path:
        path, filename = relative_path.rsplit('/', 1)
    else:
        path, filename = '', relative_path

    parts = []
    
    # Add 'root' field
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="root"\r\n\r\n'
        f"config\r\n"
    )
    
    # Add 'path' field if present
    if path:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="path"\r\n\r\n'
            f"{path}\r\n"
        )
        
    # Add 'file' field
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    )
    
    body = b""
    for p in parts:
        body += p.encode('utf-8')
    body += file_bytes
    body += f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    return http_post(ip, "/server/files/upload?root=config", data=body, headers=headers)

def get_remote_file_content(ip, path):
    path = path.replace('\\', '/')
    url = f"http://{ip}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read()
    except Exception:
        return None

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
        
    print("Checking which files have modifications...")
    uploaded_any = False
    for full_path, rel_path in files_to_upload:
        url_rel_path = rel_path.replace('\\', '/')
        
        with open(full_path, 'rb') as f:
            local_content = f.read()
            
        remote_content = get_remote_file_content(ip, f"/server/files/config/{url_rel_path}")
        if remote_content == local_content:
            print(f"Skipping {rel_path} (no changes)")
            continue
            
        print(f"Uploading {rel_path}...")
        upload_file(ip, rel_path, local_content)
        uploaded_any = True
        
    if uploaded_any:
        print("Upload completed successfully!")
        restart_klipper(ip)
    else:
        print("All files are up-to-date. No upload needed.")

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
