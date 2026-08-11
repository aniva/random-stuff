@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo QIDI Studio Git Symlink Setup (WSL Edition)
echo ==========================================

:: Hardcode the exact WSL path here
set "gitDir=\\wsl.localhost\Ubuntu\home\me\repos\random-stuff\qidi-studio"
set "userBaseDir=%AppData%\QIDIStudio\user"

echo Target Git Repo: %gitDir%
echo.

if not exist "%userBaseDir%" (
    echo QIDI Studio user directory not found. Please run QIDI Studio at least once.
    pause
    exit /b
)

:: Loop through each subdirectory in the user folder (default, numeric accounts, etc.)
for /d %%U in ("%userBaseDir%\*") do (
    set "userFolder=%%~nxU"
    
    :: Exclude backup folders
    set "isBackup=0"
    if "!userFolder:~-7!"=="_backup" set "isBackup=1"
    
    if "!isBackup!"=="0" (
        echo.
        echo ==========================================
        echo Processing QIDI User Profile: !userFolder!
        echo ==========================================
        
        :: Loop through the three main profile folders
        for %%F in (process filament machine) do (
            set "targetDir=%userBaseDir%\!userFolder!\%%F"
            
            :: 1. Make sure the folder actually exists in your Git repo
            if not exist "%gitDir%\%%F" (
                echo Creating empty %%F folder in Git repo...
                mkdir "%gitDir%\%%F"
            )
            
            :: 2. Check what is currently in the user profile directory
            if exist "!targetDir!" (
                :: Check if it is already a symlink/junction
                fsutil reparsepoint query "!targetDir!" >nul 2>nul
                
                if !errorlevel! equ 0 (
                    echo Link already exists for %%F. Skipping...
                ) else (
                    echo Regular folder found. Backing up to %%F_backup...
                    if exist "%userBaseDir%\!userFolder!\%%F_backup" rmdir /s /q "%userBaseDir%\!userFolder!\%%F_backup"
                    move /y "!targetDir!" "%userBaseDir%\!userFolder!\%%F_backup" >nul
                    
                    echo Creating symbolic link for %%F...
                    mklink /D "!targetDir!" "%gitDir%\%%F"
                )
            ) else (
                echo Creating symbolic link for %%F...
                mklink /D "!targetDir!" "%gitDir%\%%F"
            )
        )
    )
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
pause