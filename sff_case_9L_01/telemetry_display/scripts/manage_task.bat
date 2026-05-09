@echo off
setlocal
:: Get the directory where THIS batch file is located
set "BASE_DIR=%~dp0"
title SFF Telemetry Task Manager

:MENU
cls
echo ==========================================
echo    SFF Telemetry Task Manager
echo ==========================================
echo [1] Install / Update Task
echo [2] Uninstall / Cleanup Task
echo [3] Exit
echo ==========================================
set /p choice="Select an option (1-3): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto UNINSTALL
if "%choice%"=="3" exit
goto MENU

:INSTALL
echo [*] Launching Installer...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%BASE_DIR%install_task.ps1\"'"
goto END

:UNINSTALL
echo [*] Launching Uninstaller...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%BASE_DIR%uninstall_task.ps1\"'"
goto END

:END
echo [*] If the blue window flashed and closed, check Task Scheduler.
pause
goto MENU