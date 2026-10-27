@echo off
cd /d "%~dp0"
echo ========================================================
echo                 Starting IntelliShell
echo ========================================================
echo.
ai_shell.exe ai_adapter.py
if errorlevel 1 (
    echo.
    echo Shell exited with an error.
    pause
)
