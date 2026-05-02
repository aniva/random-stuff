# ==============================================================================
# Script: erase_esp32.ps1
# Purpose: Execute full ESP32-C6 flash memory erasure via esptool
# ==============================================================================

Clear-Host
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " ESP32-C6 Nuclear Erase Protocol" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "WARNING: This operation will completely wipe the flash memory.`n" -ForegroundColor Yellow

Write-Host "PRE-FLIGHT CHECK:" -ForegroundColor White
Write-Host "1. Ensure the module is connected via USB."
Write-Host "2. If the module is trapped in a WDT boot-loop, force Download Mode:"
Write-Host "   -> Hold BOOT button"
Write-Host "   -> Short press RST button"
Write-Host "   -> Release BOOT button`n"

Pause

Write-Host "`nExecuting PlatformIO Erase Target..." -ForegroundColor Cyan
& "$env:USERPROFILE\.platformio\penv\Scripts\python.exe" -m platformio run --target erase

Write-Host "`n[POST-ERASE ACTION REQUIRED]" -ForegroundColor Red
Write-Host "Delete the hidden '.pio' directory in the project root before initiating a new build." -ForegroundColor White
Write-Host "Press physical RST button on the board after the next successful upload.`n"

Pause