@echo off
title ThunderFit Ad Studio
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Opening ThunderFit Ad Studio in your browser...
echo   Keep this window open while using the app.
echo   Close this window to stop the app.
echo ============================================================
echo.

python -m streamlit run scripts\app.py
pause
