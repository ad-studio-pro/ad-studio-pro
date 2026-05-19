@echo off
title Fix broken Git folder
cd /d "%~dp0"

echo Removing broken .git folder...
if exist .git rmdir /s /q .git
echo Done. Now run 1_INIT_GIT.bat
pause
