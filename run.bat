@echo off
setlocal enabledelayedexpansion
title JalRakshak NCR - Gurugram Flood Command & AI Dispatch
cd /d "%~dp0"

cls
echo ===============================================================================
echo   JalRakshak NCR -- Gurugram Flood Prevention & Multi-Agency Command
echo   Team NeerNetra ^| SustainX 2026: The Sustainability Hackathon
echo   Lead ^& Backend Engineer: Kamal Shukla
echo ===============================================================================
echo.
echo   [ALL 7 PHASES OPERATIONAL]
echo    * Phase 1: SQLite Persistence, Bcrypt ^& JWT Auth in HTTP-only Cookies
echo    * Phase 2: Hotspots Telemetry, Master 36 Drains ^& Weather Scenario Engine
echo    * Phase 3: WebSocket Live Siren Alarms ^& Nearest-Unit Vehicle Dispatch
echo    * Phase 4: Dijkstra Dynamic Flood Routing ^& Vehicle Wading Profiles
echo    * Phase 5: Crowdsourced Jal-Doot Hazard Tagging ^& Computer Vision Filter
echo    * Phase 6: DHBVN 11kV Grid Cuts, Underpass Boom Barriers ^& PDF Generator
echo    * Phase 7: PWA Offline Service Worker, Bilingual (Hindi/EN) ^& Contrast Mode
echo.
echo ===============================================================================
echo.

set "PY_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "!PY_EXE!" (
    where uv >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [*] Starting via uv runtime...
        start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"
        uv run python backend\main.py
        exit /b 0
    )
    set "PY_EXE=python"
)

echo [*] Python Runtime: !PY_EXE!
echo [*] Booting FastAPI backend on http://127.0.0.1:8000 ...
echo [*] Launching interactive dashboard in your default browser...
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"

"!PY_EXE!" backend\main.py

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [!] Server session closed or encountered an error.
    pause
)
