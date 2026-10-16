Write-Host "Starting AyurClinical RAG Pipeline..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor DarkGray

$root = $PSScriptRoot

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers launched successfully!" -ForegroundColor Green
Write-Host "Backend API: http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)" -ForegroundColor Yellow
Write-Host "Frontend UI: http://127.0.0.1:5173" -ForegroundColor Cyan
