# --- Configuration ---
$TaskName   = "SFF_Telemetry_Daemon"
$ScriptPath = "D:\Users\me\Documents\projects\random-stuff\sff_case_9L_01\telemetry_display\scripts\telemetry_stream.py"

Write-Host "[*] Locating PythonW..." -ForegroundColor Cyan
$PythonW = Get-Command pythonw -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source

if (-not $PythonW) {
    Write-Host "[!] ERROR: pythonw.exe not found in PATH." -ForegroundColor Red
    exit
}

Write-Host "[*] Registering task: $TaskName" -ForegroundColor Cyan

# Define the Action (Calling PythonW directly with the script path)
$Action = New-ScheduledTaskAction -Execute "$PythonW" -Argument "`"$ScriptPath`""

# Define the Trigger (At Logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Define the Principal (Run as Admin)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Define Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register the Task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

Write-Host "[+] SUCCESS: Task registered in root library." -ForegroundColor Green