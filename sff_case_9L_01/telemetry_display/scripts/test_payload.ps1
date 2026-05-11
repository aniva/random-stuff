param (
    [int]$CpuTemp = 65,
    [int]$FanRpm = 2500,
    [int]$GpuTemp = 55,
    [int]$SsdTemp = 48,
    [int]$CpuLoad = 30,
    [int]$GpuLoad = 85,
    [int]$Brightness = 255,
    [string]$Port = "COM3"
)

$payload = "<T:$CpuTemp,R:$FanRpm,G:$GpuTemp,M:$SsdTemp,C:$CpuLoad,L:$GpuLoad,B:$Brightness>"
Write-Output "Injecting payload: $payload into $Port..."

try {
    $serial = New-Object System.IO.Ports.SerialPort $Port, 115200, 'None', 8, 'One'
    
    # CRITICAL FIX: Keep DTR/RTS False so the auto-reset circuit is bypassed
    $serial.DtrEnable = $false
    $serial.RtsEnable = $false
    
    $serial.Open()
    Start-Sleep -Milliseconds 500  
    
    $serial.Write($payload)        
    
    Start-Sleep -Milliseconds 100 
    $serial.Close()
    
    Write-Output "Transmission successful. Screen should now update."
}
catch {
    Write-Error "Transmission failed. Target port $Port is locked."
}