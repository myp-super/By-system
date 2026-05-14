@echo off
title 保研全程管理 Server
cd /d "%~dp0"
echo ================================================
echo   保研全程管理 v4 — Production Server
echo   http://localhost:5000
echo ================================================
echo.
echo   Press Ctrl+C to stop the server
echo.
python run.py
pause
