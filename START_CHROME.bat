@echo off
title ThunderFit - Chrome (port 9224)
setlocal
cd /d "%~dp0"

if "%CDP_PORT%"=="" set "CDP_PORT=9224"

echo.
echo === Opening dedicated Chrome for ThunderFit Ad Studio ===
echo Port    : %CDP_PORT%
echo Profile : %USERPROFILE%\thunderfit-cdp-profile
echo.
echo This is a NEW Chrome window separate from your normal Chrome
echo and from any other ad-builder Chrome on port 9223.
echo.

set "CHROME_EXE="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

if "%CHROME_EXE%"=="" (
    echo [ERROR] chrome.exe not found in standard locations.
    pause & exit /b 1
)

set "CDP_PROFILE=%USERPROFILE%\thunderfit-cdp-profile"
if not exist "%CDP_PROFILE%" mkdir "%CDP_PROFILE%"

start "" "%CHROME_EXE%" --remote-debugging-port=%CDP_PORT% --remote-debugging-address=127.0.0.1 --user-data-dir="%CDP_PROFILE%" --no-default-browser-check --no-first-run https://claude.ai/new

echo Waiting 4 seconds for Chrome to start...
timeout /t 4 /nobreak >nul

echo.
echo Verifying CDP port %CDP_PORT% is listening...
netstat -ano | findstr ":%CDP_PORT%" | findstr "LISTEN"
if errorlevel 1 (
    echo.
    echo [WARN] Port %CDP_PORT% is not listening yet.
    echo If a Chrome window opened, give it 10 more seconds and run CHECK_CHROME.bat.
    echo If no window opened, see troubleshooting below.
) else (
    echo.
    echo [OK] CDP is listening on port %CDP_PORT%.
)

echo.
echo === FIRST TIME ONLY ===
echo   1. In the new Chrome window, log in to claude.ai
echo   2. Switch model to "Opus 4.7" (avoid "Adaptive")
echo   3. Keep this Chrome window OPEN while using the app
echo.
echo You can close THIS cmd window now — Chrome will keep running.
echo.
pause
