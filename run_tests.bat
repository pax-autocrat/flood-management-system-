@echo off
setlocal enabledelayedexpansion
title JalRakshak NCR - 49/49 Automated Verification Test Runner
cd /d "%~dp0"

cls
echo ===============================================================================
echo   NeerNetra ^| JalRakshak NCR Automated Verification Suite (All 7 Phases)
echo   Team: NeerNetra ^| Lead ^& Backend Engineer: Kamal Shukla
echo ===============================================================================
echo.

set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "!PY_EXE!" (
    set "PY_EXE=python"
)

echo [*] Using Python: !PY_EXE!
echo.

set "FAILED=0"

echo [1/7] Running Phase 1: Database Persistence, Bcrypt ^& JWT Auth (7 Tests)...
"!PY_EXE!" backend\test_phase1.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [2/7] Running Phase 2: Hotspots Telemetry, Master 36 Drains ^& Weather Engine (8 Tests)...
"!PY_EXE!" backend\test_phase2.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [3/7] Running Phase 3: Real-Time WebSockets, Fleet Transponders ^& Citizen SOS (8 Tests)...
"!PY_EXE!" backend\test_phase3.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [4/7] Running Phase 4: Dijkstra Flood-Aware Routing ^& Geocoding (5 Tests)...
"!PY_EXE!" backend\test_phase4.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [5/7] Running Phase 5: Crowdsourced Jal-Doot, Computer Vision ^& EXIF GPS (7 Tests)...
"!PY_EXE!" backend\test_phase5.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [6/7] Running Phase 6: Multi-Agency Grid Cuts, Boom Barriers ^& PDF Generator (7 Tests)...
"!PY_EXE!" backend\test_phase6.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

echo.
echo [7/7] Running Phase 7: PWA Offline Capabilities, Bilingual i18n ^& Speed Dial (7 Tests)...
"!PY_EXE!" backend\test_phase7.py
if !ERRORLEVEL! NEQ 0 set "FAILED=1" & goto :done

:done
echo.
if "!FAILED!"=="0" (
    echo ===============================================================================
    echo   SUCCESS: ALL 49 / 49 AUTOMATED TESTS PASSED WITH 100%% SUCCESS!
    echo   JalRakshak NCR is completely verified, hardened, and competition-ready.
    echo ===============================================================================
) else (
    echo [!] Test suite encountered an error.
)

pause
