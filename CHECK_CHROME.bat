@echo off
title Chrome CDP Diagnostic
setlocal
cd /d "%~dp0"

if "%CDP_PORT%"=="" set "CDP_PORT=9224"

echo ============================================================
echo   Chrome CDP Diagnostic — port %CDP_PORT%
echo ============================================================
echo.

echo [1] Is anything listening on port %CDP_PORT%?
echo ----------------------------------------
netstat -ano | findstr ":%CDP_PORT%" | findstr "LISTEN"
if errorlevel 1 (
    echo   NOTHING is listening on %CDP_PORT%.
    echo   -^> Chrome with CDP is NOT running. Run START_CHROME.bat.
    echo.
    goto :skip_curl
)
echo.

echo [2] Can we reach http://127.0.0.1:%CDP_PORT%/json/version ?
echo -----------------------------------------------------
curl -s -o nul -w "  HTTP %%{http_code}  (response time %%{time_total}s)\n" http://127.0.0.1:%CDP_PORT%/json/version
echo.

:skip_curl
echo [3] Chrome processes with --remote-debugging-port flag:
echo -----------------------------------------------------
wmic process where "name='chrome.exe'" get CommandLine 2>nul | findstr "remote-debugging-port"
if errorlevel 1 (
    echo   NO chrome.exe is running with --remote-debugging-port.
    echo   -^> Run START_CHROME.bat. If you already did, see fix below.
)

echo.
echo ============================================================
echo If port is not listening:
echo   1. Close ALL Chrome windows. Open Task Manager (Ctrl+Shift+Esc)
echo      and end every chrome.exe process.
echo   2. Wait 3 seconds.
echo   3. Run START_CHROME.bat again.
echo   4. Wait until you see the new Chrome window with claude.ai.
echo   5. Run CHECK_CHROME.bat again.
echo.
echo If still failing — Chrome may be installed in non-standard path.
echo ============================================================
pause
