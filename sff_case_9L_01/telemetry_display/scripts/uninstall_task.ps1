# --- Configuration ---
$TaskName = "SFF_Telemetry_Daemon"

# Check if the task exists before trying to delete it
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[+] Task '$TaskName' has been successfully removed." -ForegroundColor Cyan
} else {
    Write-Host "[!] Task '$TaskName' not found. Nothing to remove." -ForegroundColor Yellow
}