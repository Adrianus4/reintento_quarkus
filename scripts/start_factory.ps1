# scripts/start_factory.ps1
# TCS Intelligent Microservice Factory -- Distributed Cluster Launcher

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   TATA CONSULTANCY SERVICES (TCS)                          " -ForegroundColor White
Write-Host "   Intelligent Microservice Factory -- Multi-Agent Cluster   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$baseDir = Split-Path -Parent $PSScriptRoot

$services = @(
    @{ Name = "auth-access-service"; Port = 8001; Path = "$baseDir\services\auth-access-service"; Cmd = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8001" },
    @{ Name = "client-governance-service"; Port = 8002; Path = "$baseDir\services\client-governance-service"; Cmd = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8002" },
    @{ Name = "ai-orchestrator-service"; Port = 8003; Path = "$baseDir\services\ai-orchestrator-service"; Cmd = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8003" },
    @{ Name = "sandbox-verifier-service"; Port = 8004; Path = "$baseDir\services\sandbox-verifier-service"; Cmd = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8004" }
)

Write-Host "[1/5] Starting Backend Microservices..." -ForegroundColor Yellow
$processes = @()

foreach ($svc in $services) {
    Write-Host "  -> Launching $($svc.Name) on port $($svc.Port)..." -ForegroundColor Gray
    $p = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$($svc.Path)`"; $($svc.Cmd)" -PassThru
    $processes += $p
    Start-Sleep -Milliseconds 600
}

Write-Host "[2/5] Starting Frontend Workspace Studio (tcs-factory-ui)..." -ForegroundColor Yellow
$uiPath = "$baseDir\services\tcs-factory-ui"
$uiProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$uiPath`"; npm.cmd run dev" -PassThru
$processes += $uiProcess

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   CLUSTER ONLINE & ACCESSIBLE:                             " -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  - UI Workspace Studio:      http://localhost:5173" -ForegroundColor Cyan
Write-Host "  - Auth Access Service:       http://localhost:8001/api/v1/health" -ForegroundColor White
Write-Host "  - Client Governance Service: http://localhost:8002/api/v1/health" -ForegroundColor White
Write-Host "  - AI Orchestrator Service:   http://localhost:8003/api/v1/health" -ForegroundColor White
Write-Host "  - Sandbox Verifier Service:  http://localhost:8004/api/v1/health" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C or close spawned console windows to stop cluster." -ForegroundColor Gray

