@echo off
title Ad Studio Pro - Push Seed Audio voice feature
cd /d "%~dp0"
echo.
echo ============================================================
echo   Pushing Seed Audio 1.0 voice feature to GitHub
echo ============================================================
echo.
if exist ".git\index.lock" (
  echo Removing stale git lock file...
  del /f /q ".git\index.lock"
)
echo Step 1/3: Staging files...
git add scripts/seed_audio_client.py scripts/generate_audio.py scripts/audio_studio.py scripts/app.py .env.example SEED_AUDIO_README.md PUSH_AUDIO.bat
echo.
echo Step 2/3: Committing...
git -c user.email="agent1@romarketinggroup.com" -c user.name="Roi" commit -m "feat: Seed Audio 1.0 voice generation + Streamlit voice mode"
echo.
echo Step 3/3: Pushing to GitHub origin main...
git push origin main
echo.
echo ============================================================
echo   Finished. Read the messages above this line.
echo   If push succeeded: refresh the site in about 1 minute
echo   and tick the box  voice mode Seed Audio 1.0  at the top.
echo ============================================================
echo.
pause
