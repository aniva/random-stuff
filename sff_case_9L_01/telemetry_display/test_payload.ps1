param (
    [string]$Port = "COM3",
    [int]$BaudRate = 115200,
    [string]$Temp = "99",
    [string]$RPM = "4500"
)

try {
    $serial = New-Object System.IO.Ports.SerialPort $Port, $BaudRate, 'None', 8, 'One'
    $serial.Open()
    
    # Construct and send the payload
    $payload = "<T:$Temp,R:$RPM>`n"
    $serial.Write($payload)
    
    Write-Host "Success: Injected payload $payload into $Port" -ForegroundColor Green
} catch {
    Write-Host "Error: Could not open $Port." -ForegroundColor Red
    Write-Host "Ensure the Python telemetry daemon is stopped before injecting test payloads." -ForegroundColor Yellow
} finally {
    if ($serial -and $serial.IsOpen) {
        $serial.Close()
    }
}