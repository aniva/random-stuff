@echo off
title ESP32-C6 Nuclear Erase Protocol
color 0B

echo ===================================================
echo  ESP32-C6 Nuclear Erase Protocol
echo ===================================================
color 0E
echo WARNING: This operation will completely wipe the flash memory.
echo.
color 07
echo PRE-FLIGHT CHECK:
echo 1. Ensure the module is connected via USB.
echo 2. If the module is trapped in a WDT boot-loop, force Download Mode:
echo    -^> Hold BOOT button
echo    -^> Short press RST button
echo    -^> Release BOOT button
echo.
pause

echo.
echo Executing PlatformIO Erase Target...
"%USERPROFILE%\.platformio\penv\Scripts\python.exe" -m platformio run --target erase

echo.
color 0C
echo [POST-ERASE ACTION REQUIRED]
color 07
echo Delete the hidden '.pio' directory in the project root before initiating a new build.
echo Press physical RST button on the board after the next successful upload.
echo.
pause