# --- Configuration ---
$TaskName = "SFF_Telemetry_Daemon"

Write-Host "[*] Searching for all instances of $TaskName..." -ForegroundColor Cyan

# Find all tasks with this name across all folders
$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -eq $TaskName }

if ($tasks) {
    foreach ($task in $tasks) {
        # Force removal of the task and stop it if it's currently running
        Unregister-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Confirm:$false
        Write-Host "[+] Removed task from path: $($task.TaskPath)" -ForegroundColor Green
    }
    
    # Kill any lingering background processes to free up COM3
    Write-Host "[*] Cleaning up lingering processes..." -ForegroundColor Cyan
    Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
    Write-Host "[+] Cleanup Complete." -ForegroundColor Green
} else {
    Write-Host "[!] No instances of '$TaskName' found." -ForegroundColor Yellow
}