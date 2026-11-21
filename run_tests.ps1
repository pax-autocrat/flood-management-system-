# NeerNetra - 49/49 Automated Verification Test Runner (PowerShell Native)
# Team: NeerNetra | Lead & Backend Engineer: Kamal Shukla

$Host.UI.RawUI.WindowTitle = "JalRakshak NCR - 49/49 Automated Verification Test Runner"
Set-Location -Path $PSScriptRoot

Clear-Host
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  NeerNetra | JalRakshak NCR Automated Verification Suite (All 7 Phases)" -ForegroundColor Cyan
Write-Host "  Team: NeerNetra | Lead & Backend Engineer: Kamal Shukla" -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$defaultUvPython = "C:\Users\kamal\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"

$pythonExe = if (Test-Path $venvPython) {
    $venvPython
} elseif (Test-Path $defaultUvPython) {
    $defaultUvPython
} else {
    "python"
}

Write-Host "[*] Using Python: $pythonExe" -ForegroundColor Green
Write-Host ""

$phases = @(
    @{ Name = "Phase 1: Database Persistence, Bcrypt & JWT Auth (7 Tests)"; Script = "backend\test_phase1.py" },
    @{ Name = "Phase 2: Hotspots Telemetry, Master 36 Drains & Weather Engine (8 Tests)"; Script = "backend\test_phase2.py" },
    @{ Name = "Phase 3: Real-Time WebSockets, Fleet Transponders & Citizen SOS (8 Tests)"; Script = "backend\test_phase3.py" },
    @{ Name = "Phase 4: Dijkstra Flood-Aware Routing & Geocoding (5 Tests)"; Script = "backend\test_phase4.py" },
    @{ Name = "Phase 5: Crowdsourced Jal-Doot, Computer Vision & EXIF GPS (7 Tests)"; Script = "backend\test_phase5.py" },
    @{ Name = "Phase 6: Multi-Agency Grid Cuts, Boom Barriers & PDF Generator (7 Tests)"; Script = "backend\test_phase6.py" },
    @{ Name = "Phase 7: PWA Offline Capabilities, Bilingual i18n & Speed Dial (7 Tests)"; Script = "backend\test_phase7.py" }
)

$allPassed = $true
$idx = 1
foreach ($phase in $phases) {
    Write-Host "-------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[$idx/7] Running $($phase.Name)..." -ForegroundColor Yellow
    Write-Host "-------------------------------------------------------------------------------" -ForegroundColor DarkGray
    & $pythonExe $phase.Script
    if ($LASTEXITCODE -ne 0) {
        $allPassed = $false
        Write-Host ""
        Write-Host "[!] $($phase.Name) FAILED (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        break
    }
    Write-Host ""
    $idx++
}

if ($allPassed) {
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: ALL 49 / 49 AUTOMATED TESTS PASSED WITH 100% SUCCESS!" -ForegroundColor Green
    Write-Host "  JalRakshak NCR is completely verified, hardened, and competition-ready." -ForegroundColor White
    Write-Host "===============================================================================" -ForegroundColor Green
} else {
    Write-Host "[!] Some tests failed. Please review the output above." -ForegroundColor Red
}

Read-Host "Press Enter to exit..."
