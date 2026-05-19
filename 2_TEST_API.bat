@echo off
title ThunderFit - Test API
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ThunderFit - Step 2: BytePlus connection test
echo   Sending a tiny 5-second test task to verify your API key.
echo ============================================================
echo.

python scripts\test_connection.py

echo.
echo ============================================================
echo   If you saw  [OK] Task submitted: ...
echo   then your API key works! Next: double-click  3_TEST_FULL.bat
echo ============================================================
pause
