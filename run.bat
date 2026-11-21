@echo off
setlocal enabledelayedexpansion
title NeerNetra - AI Urban Flood Intelligence & Rescue Command
cd /d "%~dp0"

cls
echo ===============================================================================
echo   NeerNetra -- AI Urban Flood Intelligence & Multi-Agency Rescue Command
echo   Municipal Corporation of Gurugram (MCG) & SDRF Response Grid
echo   Lead Engineer: Kamal Shukla ^| Team NeerNetra ^| SustainX 2026
echo ===============================================================================
echo.
echo   [SYSTEM CAPABILITIES ONLINE]
echo    * Full-Stack AI Flood Intelligence: 159 Hotspots, Master 36 Drains
echo    * Explainable ML Engine: Random Forest Flood Classification & Depth Regression
echo    * Citizen SOS Distress Dispatch: Dual-Channel SMS / BLE Mesh Fallback
echo    * Dynamic Spatial Routing: Dijkstra Flood-Aware Elevation Routing
echo    * Crowdsourced Jal-Doot: Computer Vision Surface Water Verification
echo    * Multi-Agency Grid: DHBVN 11kV Substation Safety & Underpass Boom Barriers
echo    * PWA Offline Service Worker: Bilingual (Hindi/English) & High Contrast
echo.
echo ===============================================================================
echo.

set "PY_EXE="

:: 1. Check local virtual environment (.venv)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
)

:: 2. Check uv package manager
if not defined PY_EXE (
    where uv >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [*] Detected uv package manager. Launching via uv...
        echo [*] Auto-opening http://127.0.0.1:8000 in your browser...
        start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"
        uv run python backend\main.py
        goto :done
    )
)

:: 3. Check system Python
if not defined PY_EXE (
    where python >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=python"
    )
)

if not defined PY_EXE (
    echo [ERROR] Python 3.10+ was not found on your system!
    echo Please install Python from https://www.python.org/ or install uv.
    echo.
    pause
    exit /b 1
)

echo [*] Python Runtime: !PY_EXE!
echo [*] Checking dependencies...
"!PY_EXE!" -c "import fastapi, uvicorn, pydantic, sklearn, PIL, reportlab" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [*] Installing required packages from requirements.txt...
    "!PY_EXE!" -m pip install -r requirements.txt
)

echo [*] Booting NeerNetra Backend on http://127.0.0.1:8000 ...
echo [*] Auto-opening http://127.0.0.1:8000 in your browser...
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

"!PY_EXE!" backend\main.py

:done
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [!] Server session stopped or encountered an error.
    pause
)
