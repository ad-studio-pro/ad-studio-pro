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

REM ── SAFETY NET 1: verify app.py syntax before doing anything ──
echo === Verifying app.py syntax... ===
python -c "import ast; ast.parse(open('scripts/app.py', encoding='utf-8').read()); print('OK')" 2>&1
if errorlevel 1 (
    echo.
    echo [ABORT] scripts/app.py has a syntax error — refusing to push broken code.
    echo Close any editor that has app.py open, then run this script again.
    pause
    exit /b 1
)
echo.

REM Stage every change — single `git add -A` is safer than enumerating files
REM (enumerating risks re-staging stale content from old runs).
git add -A

echo.
echo === Files staged: ===
git diff --cached --name-only
echo.

REM ── SAFETY NET 2: verify staged app.py also passes syntax ──
git show :scripts/app.py > "%TEMP%\_staged_app.py" 2>nul
if exist "%TEMP%\_staged_app.py" (
    python -c "import ast; ast.parse(open(r'%TEMP%\_staged_app.py', encoding='utf-8').read()); print('Staged app.py OK')" 2>&1
    if errorlevel 1 (
        echo.
        echo [ABORT] The STAGED version of app.py is broken. Unstaging and aborting.
        git reset HEAD scripts/app.py
        del "%TEMP%\_staged_app.py"
        pause
        exit /b 1
    )
    del "%TEMP%\_staged_app.py"
)
echo.

git commit -m "chore: push latest local changes"

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
echo Wait ~30-60 seconds, then refresh the app p