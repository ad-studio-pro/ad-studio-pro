@echo off
REM ============================================================
REM PUSH FIX TO STREAMLIT CLOUD
REM ------------------------------------------------------------
REM Commits the lazy-secrets fix and pushes to GitHub.
REM Streamlit Cloud will auto-redeploy in ~30-60 seconds.
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo === Pushing fix to GitHub (Streamlit Cloud auto-redeploys) ===
echo.

REM Make sure we're on a clean clone
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This folder is not a git repository.
    echo Run 1_INIT_GIT.bat first.
    pause
    exit /b 1
)

REM Stage every change inside scripts/ + app.py
git add scripts/byteplus_client.py
git add scripts/anthropic_client.py
git add scripts/upload_image.py
git add scripts/stage1_research.py
git add scripts/nano_banana.py
git add scripts/app.py
git add scripts/auth_gate.py
git add requirements.txt
git add GOOGLE_OAUTH_SETUP.md
git add .python-version
git add runtime.txt
git add 3_PUSH_FIX.bat

echo.
echo === Files staged: ===
git diff --cached --name-only
echo.

git commit -m "feat: custom stateless OAuth (HMAC-signed state)" -m "Replaced Streamlit's st.login() with our own Google OAuth flow that uses HMAC-signed state instead of session storage. This sidesteps the MismatchingStateError bug in Streamlit Cloud's multi-replica setup. Redirect URI changes from /oauth2callback to / (the app root). Also drops Authlib dependency."

if errorlevel 1 (
    echo.
    echo [INFO] Nothing new to commit, or commit failed.
    echo Trying to push anyway in case there are unpushed commits...
)

echo.
echo === Pushing to origin/main ===
git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Check the message above.
    echo If it asks for credentials, use your GitHub username + personal access token.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [OK] Fix pushed. Streamlit Cloud is rebuilding...
echo ============================================================
echo.
echo Watch the rebuild here:
echo   https://share.streamlit.io/
echo.
echo Or your app URL directly:
echo   https://ad-studio-pro.streamlit.app/
echo.
echo Wait ~30-60 seconds, then refresh the app page.
echo.
pause
