@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0汉化工具\install.ps1" -Action uninstall
set "ZFY_RESULT=%errorlevel%"
pause
exit /b %ZFY_RESULT%
