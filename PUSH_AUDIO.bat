@echo off
title Ad Studio Pro - Push Seed Audio voice feature
cd /d "%~dp0"
echo.
echo ============================================================
echo   Pushing Seed Audio voice feature to GitHub
echo ============================================================
echo.
if exist ".git\index.lock" (
  echo Removing stale git lock file...
  del /f /q ".git\index.lock"
)
echo Step 1/4: Staging files...
git add scripts/seed_audio_client.py scripts/generate_audio.py scripts/audio_studio.py scripts/app.py .env.example SEED_AUDIO_README.md PUSH_AUDIO.bat
echo.
echo Step 2/4: Committing (it is OK if it says "nothing to commit")...
git -c user.email="agent1@romarketinggroup.com" -c user.name="Roi" commit -m "feat: Seed Audio voice generation + Streamlit voice mode"
echo.
echo Step 3/4: Syncing with GitHub (pull remote changes)...
git -c user.email="agent1@romarketinggroup.com" -c user.name="Roi" pull --no-rebase --no-edit origin main
echo.
echo Step 4/4: Pushing to GitHub origin main...
git push origin main
echo.
echo ============================================================
echo   Finished. Read the messages above this line.
echo   If it says pushed / up to date, refresh the site in about
echo   1 minute and try again.
echo ============================================================
echo.
pause
