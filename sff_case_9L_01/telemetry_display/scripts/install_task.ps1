# --- Configuration ---
$TaskName   = "SFF_Telemetry_Daemon"
$ScriptPath = "D:\Users\me\Documents\projects\random-stuff\sff_case_9L_01\telemetry_display\scripts\telemetry_stream.py"

# --- 1. Pre-Flight Checks ---
Write-Host "[*] Locating PythonW..." -ForegroundColor Cyan
$PythonW = Get-Command pythonw -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source

if (-not $PythonW) {
    Write-Host "[!] ERROR: pythonw.exe not found in PATH." -ForegroundColor Red
    exit
}

# --- 2. Cleanup Existing Instances (Atomic Prevention) ---
Write-Host "[*] Cleaning up existing telemetry instances..." -ForegroundColor Cyan

# Stop and Unregister any existing version of the task
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-ScheduledTask -TaskName $_.TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
    Write-Host "[+] Removed old task registration." -ForegroundColor Gray
}

# Kill any background pythonw instances to free up COM3
Write-Host "[*] Freeing up COM port..." -ForegroundColor Cyan
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue

# --- 3. Registration ---
Write-Host "[*] Registering task: $TaskName" -ForegroundColor Cyan

# Define the Action (Calling PythonW directly with the script path)
$Action = New-ScheduledTaskAction -Execute "$PythonW" -Argument "`"$ScriptPath`""

# Define the Trigger (At Logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Define the Principal (Run as Admin)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Define Settings (Important for SFF portability)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register the Task in the root library
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "[+] SUCCESS: Task registered in root library." -ForegroundColor Green

# --- 4. Immediate Activation ---
Write-Host "[*] Starting telemetry stream now..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName
Write-Host "[+] All systems active. Check ESP32 display." -ForegroundColor Green