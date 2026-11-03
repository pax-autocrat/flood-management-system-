@echo off
title JalRakshak NCR - Flood Management System
cd /d "%~dp0backend"

echo =====================================================================
echo           JalRakshak NCR - Flood Prevention ^& Rescue App
echo                     Municipal Corporation Gurugram
echo =====================================================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend\.venv\
    echo Please make sure the backend dependencies are installed.
    echo.
    pause
    exit /b 1
)

echo [*] Starting FastAPI Backend Server on http://127.0.0.1:8000...
echo [*] Opening JalRakshak NCR Web App in your default browser...
echo.

:: Automatically open browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

:: Start Uvicorn Server via Python venv
.venv\Scripts\python.exe run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server terminated unexpectedly with error code %ERRORLEVEL%.
    pause
)
