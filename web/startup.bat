@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =====================================
echo   保研全程管理 Web v3.0 — 生产模式
echo =====================================
echo.
echo   启动中... http://localhost:5000
echo   按 Ctrl+C 停止服务
echo.
python app.py --prod
pause
