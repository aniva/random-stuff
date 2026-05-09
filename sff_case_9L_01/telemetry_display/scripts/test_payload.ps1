param (
    [int]$Temp = 65,
    [int]$Rpm = 2500,
    [string]$Port = "COM3"
)

$payload = "<T:$Temp,R:$Rpm>"
Write-Output "Injecting payload: $payload into $Port..."

try {
    $serial = New-Object System.IO.Ports.SerialPort $Port, 115200, 'None', 8, 'One'
    $serial.Open()
    $serial.WriteLine($payload)
    $serial.Close()
    Write-Output "Transmission successful."
}
catch {
    Write-Error "Failed to transmit. Ensure $Port is not locked by the PlatformIO Serial Monitor."
}