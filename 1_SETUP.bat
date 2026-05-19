@echo off
title ThunderFit - Setup
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ThunderFit - First-time setup (run only once)
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not installed.
    echo Install from https://www.python.org/downloads/ and check "Add Python to PATH".
    pause & exit /b 1
)
python --version
echo.

echo [..] Installing required packages...
python -m pip install --user --upgrade pip
python -m pip install --user requests python-dotenv pillow streamlit playwright imageio-ffmpeg google-genai tavily-python
if errorlevel 1 (
    echo [ERROR] Failed to install packages.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   [OK] Setup done!
echo.
echo   Next steps:
echo     1. START_CHROME.bat  - Opens Chrome with claude.ai
echo                            Log in once with your Claude account.
echo     2. APP_START.bat     - Opens the ad studio in your browser.
echo ============================================================
pause
