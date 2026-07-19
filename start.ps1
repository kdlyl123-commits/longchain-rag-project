$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RAG Knowledge Base Q&A System" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:3000"
Write-Host ""
Write-Host "  Close the popup windows to stop."
Write-Host ""

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; Write-Host 'Backend starting...' -ForegroundColor Green; python -m uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; Write-Host 'Frontend starting...' -ForegroundColor Green; npm run dev"

Start-Sleep -Seconds 4
Start-Process "http://localhost:3000"

Write-Host "Done! Opening browser..." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this window"
