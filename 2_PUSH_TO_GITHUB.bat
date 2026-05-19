@echo off
title Ad Studio Pro - Push to GitHub
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Push to GitHub (after creating private repo)
echo ============================================================
echo.

if not exist .git (
    echo [ERROR] Git not initialized. Run 1_INIT_GIT.bat first.
    pause & exit /b 1
)

echo Step 1: Create a PRIVATE repo at: https://github.com/new
echo         Name: ad-studio-pro
echo         Visibility: PRIVATE  (important - we have API keys!)
echo         DO NOT initialize with README/license (leave empty)
echo.
echo Step 2: Copy the repository URL from GitHub.
echo         It looks like:  https://github.com/YOUR_USERNAME/ad-studio-pro.git
echo.

set /p REPO_URL="Paste the URL and press Enter: "

if "%REPO_URL%"=="" (
    echo No URL provided. Run again when ready.
    pause & exit /b 1
)

echo.
echo Pushing to %REPO_URL% ...
echo.

git remote remove origin 2>nul
git remote add origin %REPO_URL%
git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Possible reasons:
    echo   - You weren't authenticated to GitHub yet (sign in via browser)
    echo   - The repo URL is wrong
    echo   - The repo already has content
    echo.
    pause & exit /b 1
)

echo.
echo ============================================================
echo   [OK] Code pushed to GitHub!
echo.
echo   Next: deploy to Streamlit Cloud
echo   1. Go to https://share.streamlit.io/
echo   2. Sign in with GitHub
echo   3. New app - From existing repo
echo   4. Pick ad-studio-pro, main file = scripts/app.py
echo   5. Click Deploy
echo   6. Once deployed: Settings - Secrets - paste your keys
echo ============================================================
pause
