@echo off
title ThunderFit - Export Project
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ThunderFit Ad Studio — Export Package
echo ============================================================
echo.

set "STAMP=%date:~-4%%date:~-10,2%%date:~-7,2%"
set "ZIP_NAME=thunderfit-ads-export-%STAMP%.zip"
set "ZIP_PATH=%USERPROFILE%\Documents\%ZIP_NAME%"

echo Building ZIP at: %ZIP_PATH%
echo.

REM Use PowerShell to create the zip — handles long paths + UTF-8 properly
REM Excludes: outputs/videos (heavy), outputs/logs, __pycache__, venv
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src = '%~dp0'.TrimEnd('\'); ^
     $dst = '%ZIP_PATH%'; ^
     if (Test-Path $dst) { Remove-Item $dst -Force }; ^
     $exclude = @('outputs', 'venv', '__pycache__', '.git', 'thunderfit-cdp-profile'); ^
     $items = Get-ChildItem -Path $src -Recurse -Force | ^
              Where-Object { ^
                  $rel = $_.FullName.Substring($src.Length + 1); ^
                  $top = ($rel -split '\\')[0]; ^
                  ($exclude -notcontains $top) -and ^
                  ($_.Name -ne '__pycache__') -and ^
                  ($_.Extension -ne '.pyc') ^
              }; ^
     Compress-Archive -Path ($items.FullName) -DestinationPath $dst -CompressionLevel Optimal -Force"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create the zip.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   [OK] Export ready!
echo.
echo   File: %ZIP_PATH%
echo.
echo   What is included:
echo     - All scripts (app.py, prompt_generator.py, byteplus_client.py, ...)
echo     - All .bat launchers
echo     - All prompts/ folder contents
echo     - All assets/product/ images
echo     - .env (with YOUR keys — see warning below)
echo     - .env.example (clean template)
echo     - HANDOFF.md (instructions for the recipient)
echo     - README.md, requirements.txt
echo.
echo   What is EXCLUDED:
echo     - outputs/videos/ (the generated MP4s — heavy)
echo     - outputs/logs/
echo     - venv/ and __pycache__/
echo.
echo   ⚠ NOTE: .env contains YOUR API keys (BytePlus, imgbb).
echo   The recipient will be using YOUR billing if they don't replace them.
echo   To send WITHOUT your keys: open the zip, delete .env from inside it.
echo ============================================================
echo.
echo Open Documents folder?
pause
explorer "%USERPROFILE%\Documents"
