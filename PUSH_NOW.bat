@echo off
REM ============================================================
REM PUSH_NOW.bat v2 — bypass working tree, push HEAD directly
REM Also restores working tree from HEAD to overwrite editor garbage
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo =====================================================
echo  Step 1/5: Where are we?
echo =====================================================
echo Current directory: %CD%
echo Local HEAD:
git rev-parse HEAD
echo.

echo =====================================================
echo  Step 2/5: Restore working tree from HEAD
echo =====================================================
echo (this overwrites any editor-saved broken garbage with the clean committed version)
git checkout HEAD -- scripts/app.py
if errorlevel 1 (
    echo [ERROR] git checkout failed
    pause
    exit /b 1
)
echo Done.
echo.

echo =====================================================
echo  Step 3/5: Verify HEAD commit's app.py is clean
echo =====================================================
git show HEAD:scripts/app.py > "%TEMP%\_head_app.py" 2>nul
python -c "import ast; ast.parse(open(r'%TEMP%\_head_app.py', encoding='utf-8').read()); print('OK - HEAD commit app.py parses clean')" 2>&1
set HEAD_OK=%ERRORLEVEL%
del "%TEMP%\_head_app.py" 2>nul
if %HEAD_OK% NEQ 0 (
    echo.
    echo [ABORT] HEAD commit has broken app.py. Something went wrong locally.
    pause
    exit /b 1
)
echo.

echo =====================================================
echo  Step 4/5: What we're about to push
echo =====================================================
git fetch origin main 2>&1
echo.
echo Local HEAD:
git rev-parse main
echo Origin HEAD:
git rev-parse origin/main
echo.
echo Commits to push:
git log origin/main..main --oneline
echo.

echo =====================================================
echo  Step 5/5: Push to GitHub
echo =====================================================
git push origin main 2>&1
set PUSH_EXIT=%ERRORLEVEL%
echo.
echo === Push exit code: %PUSH_EXIT% ===
if %PUSH_EXIT% NEQ 0 (
    echo.
    echo [FAIL] Push failed. Look at the message above.
    echo Likely causes:
    echo   - No internet
    echo   - Git credentials expired -- will prompt for username + Personal Access Token
    echo   - GitHub rejected the push (unlikely)
) else (
    echo.
    echo SUCCESS! Streamlit Cloud will rebuild in ~30-60 seconds.
    echo Refresh: https://ad-studio-pro.streamlit.app/
)
echo.

echo =====================================================
echo  Done. Press any key to close.
echo =====================================================
pause
