@echo off
title IntelliShell Web Console
cd /d "%~dp0"

echo =======================================================
echo           IntelliShell Web Terminal UI
echo =======================================================
echo.
echo Opening browser at http://localhost:5000 ...
start http://localhost:5000

echo Starting Python Backend Server...
python web_server.py

pause
