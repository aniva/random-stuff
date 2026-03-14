@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo QIDI Studio Git Symlink Setup (WSL Edition)
echo ==========================================

:: Hardcode the exact WSL path here
set "gitDir=\\wsl.localhost\Ubuntu\home\me\repos\random-stuff\qidi-studio"
set "appDataDir=%AppData%\QIDIStudio\user\default"

echo Target AppData: %appDataDir%
echo Target Git Repo: %gitDir%
echo.

:: Ensure the base AppData folder exists
if not exist "%appDataDir%" (
    echo Creating missing QIDI Studio user directory...
    mkdir "%appDataDir%"
)

:: Loop through the three main profile folders
for %%F in (process filament machine) do (
    echo.
    echo --- Processing: %%F ---

    :: 1. Make sure the folder actually exists in your Git repo
    if not exist "%gitDir%\%%F" (
        echo Creating empty %%F folder in Git repo...
        mkdir "%gitDir%\%%F"
    )

    :: 2. Check what is currently in AppData
    if exist "%appDataDir%\%%F" (
        :: Check if it is already a symlink/junction
        fsutil reparsepoint query "%appDataDir%\%%F" >nul 2>nul
        
        if !errorlevel! equ 0 (
            echo Link already exists for %%F. Skipping...
        ) else (
            echo Regular folder found. Backing up to %%F_backup...
            if exist "%appDataDir%\%%F_backup" rmdir /s /q "%appDataDir%\%%F_backup"
            move /y "%appDataDir%\%%F" "%appDataDir%\%%F_backup" >nul
            
            echo Creating symbolic link for %%F...
            mklink /D "%appDataDir%\%%F" "%gitDir%\%%F"
        )
    ) else (
        echo Creating symbolic link for %%F...
        mklink /D "%appDataDir%\%%F" "%gitDir%\%%F"
    )
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
pause