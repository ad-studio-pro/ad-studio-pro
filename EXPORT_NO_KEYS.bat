@echo off
title ThunderFit - Export (no API keys)
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ThunderFit Ad Studio — Export WITHOUT your API keys
echo ============================================================
echo.

set "STAMP=%date:~-4%%date:~-10,2%%date:~-7,2%"
set "ZIP_NAME=thunderfit-ads-export-NOKEYS-%STAMP%.zip"
set "ZIP_PATH=%USERPROFILE%\Documents\%ZIP_NAME%"

echo Building ZIP at: %ZIP_PATH%
echo The recipient will need to add THEIR OWN keys to .env.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src = '%~dp0'.TrimEnd('\'); ^
     $dst = '%ZIP_PATH%'; ^
     if (Test-Path $dst) { Remove-Item $dst -Force }; ^
     $exclude = @('outputs', 'venv', '__pycache__', '.git', 'thunderfit-cdp-profile'); ^
     $excludeFiles = @('.env'); ^
     $items = Get-ChildItem -Path $src -Recurse -Force | ^
              Where-Object { ^
                  $rel = $_.FullName.Substring($src.Length + 1); ^
                  $top = ($rel -split '\\')[0]; ^
                  ($exclude -notcontains $top) -and ^
                  ($excludeFiles -notcontains $_.Name) -and ^
                  ($_.Name -ne '__pycache__') -and ^
                  ($_.Extension -ne '.pyc') ^
              }; ^
     Compress-Archive -Path ($items.FullName) -DestinationPath $dst -CompressionLevel Optimal -Force"

if errorlevel 1 (
    echo [ERROR] Failed to create the zip.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   [OK] Clean export ready (no API keys included).
echo.
echo   File: %ZIP_PATH%
echo.
echo   Instructions for the recipient:
echo     1. Extract the zip
echo     2. Copy  .env.example  to  .env
echo     3. Fill in their own ARK_API_KEY and IMGBB_API_KEY
echo     4. Run 1_SETUP.bat
echo ============================================================
echo.
pause
explorer "%USERPROFILE%\Documents"
