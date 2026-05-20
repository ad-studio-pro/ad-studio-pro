@echo off
REM Recover scripts/app.py from the last committed version (origin/main).
REM Run this if Claude's editor got the file into a broken state.

setlocal
cd /d "%~dp0"

echo.
echo === Recovering scripts/app.py from git origin/main ===
echo.

git fetch origin main
if errorlevel 1 (
    echo [ERROR] git fetch failed.
    pause
    exit /b 1
)

git checkout origin/main -- scripts/app.py
if errorlevel 1 (
    echo [ERROR] git checkout failed.
    pause
    exit /b 1
)

echo.
echo [OK] scripts/app.py restored to the GitHub version.
echo You can now re-run the app and ask Claude to re-apply changes carefully.
echo.
pause
