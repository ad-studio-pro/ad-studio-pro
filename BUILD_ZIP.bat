@echo off
title Ad Studio Pro - Build Export ZIP
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Building distribution zip (your videos stay safe)
echo ============================================================
echo.

set "STAMP=%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%"
set "STAMP=%STAMP: =0%"
set "ZIP_FULL=%USERPROFILE%\Documents\ad-studio-pro-FULL-%STAMP%.zip"
set "ZIP_NOKEYS=%USERPROFILE%\Documents\ad-studio-pro-NOKEYS-%STAMP%.zip"

echo Creating FULL (with API keys) -> %ZIP_FULL%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src='%~dp0'.TrimEnd('\\'); $dst='%ZIP_FULL%'; if (Test-Path $dst) {Remove-Item $dst -Force}; ^
     $items = Get-ChildItem -Path $src -Recurse -Force | ^
        Where-Object { ^
            $rel = $_.FullName.Substring($src.Length + 1); ^
            ($rel -notlike 'outputs\videos\*.mp4') -and ^
            ($rel -notlike 'outputs\logs\*.json') -and ^
            ($rel -notlike 'outputs\thumbnails\*') -and ^
            ($rel -notlike 'venv\*') -and ^
            ($rel -notlike '*\__pycache__\*') -and ^
            ($_.Extension -ne '.pyc') ^
        }; ^
     Compress-Archive -Path $items.FullName -DestinationPath $dst -Force"

echo Creating NOKEYS (no .env) -> %ZIP_NOKEYS%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src='%~dp0'.TrimEnd('\\'); $dst='%ZIP_NOKEYS%'; if (Test-Path $dst) {Remove-Item $dst -Force}; ^
     $items = Get-ChildItem -Path $src -Recurse -Force | ^
        Where-Object { ^
            $rel = $_.FullName.Substring($src.Length + 1); ^
            ($_.Name -ne '.env') -and ^
            ($rel -notlike 'outputs\videos\*.mp4') -and ^
            ($rel -notlike 'outputs\logs\*.json') -and ^
            ($rel -notlike 'outputs\thumbnails\*') -and ^
            ($rel -notlike 'venv\*') -and ^
            ($rel -notlike '*\__pycache__\*') -and ^
            ($_.Extension -ne '.pyc') ^
        }; ^
     Compress-Archive -Path $items.FullName -DestinationPath $dst -Force"

echo.
echo ============================================================
echo   Done. Your outputs/ folder is UNTOUCHED.
echo.
echo   Files in %%USERPROFILE%%\Documents\
echo.
pause
explorer "%USERPROFILE%\Documents"
