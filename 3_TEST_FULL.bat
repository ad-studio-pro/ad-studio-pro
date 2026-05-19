@echo off
title ThunderFit - Full Pipeline Test
setlocal
cd /d "%~dp0"

echo ============================================================
echo   ThunderFit - Step 3: Full pipeline test
echo   Generates a test video (BytePlus apple-tea demo).
echo   Tests: references + image + video + audio + download.
echo   Cost: 1 generation. Takes 1-3 minutes.
echo ============================================================
echo.

python scripts\test_full_pipeline.py

echo.
echo ============================================================
echo   If you saw  [DONE] Smoke test passed.
echo   the system works end-to-end! Open outputs\videos\ to watch it.
echo ============================================================
pause
