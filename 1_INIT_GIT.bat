@echo off
title Ad Studio Pro - Initialize Git Repository
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Initialize Git Repository (run once)
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git not installed. Install from https://git-scm.com/download/win
    pause & exit /b 1
)

REM Check if .git exists and works
if exist .git (
    git status >nul 2>nul
    if errorlevel 1 (
        echo Found broken .git folder - cleaning and reinitializing...
        rmdir /s /q .git
    ) else (
        echo Git already initialized and working.
        git status
        echo.
        echo If you want to re-init from scratch, manually delete the .git folder and run again.
        pause & exit /b 0
    )
)

REM Fresh init
git init
git branch -M main
git config user.email "agent1@romarketinggroup.com"
git config user.name "Roi Cohen"

REM Stage everything respecting .gitignore
git add .

REM Verify .env / auth_config.yaml NOT staged
git ls-files --cached | findstr /R "^\.env$ ^auth_config\.yaml$" >nul
if not errorlevel 1 (
    echo.
    echo [ERROR] .env or auth_config.yaml is staged - would leak secrets!
    pause & exit /b 1
)

REM First commit
git commit -m "Initial commit - Ad Studio Pro"

echo.
echo ============================================================
echo   [OK] Git initialized and first commit created
echo.
git ls-files | find /c /v ""
echo   files committed (no .env, no auth_config.yaml, no MP4s)
echo.
echo   Next: double-click 2_PUSH_TO_GITHUB.bat
echo ============================================================
pause
