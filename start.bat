@echo off
echo Starting AyurClinical RAG Pipeline...
echo ====================================

start "AyurClinical Backend (FastAPI)" cmd /k "cd /d %~dp0\backend && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

start "AyurClinical Frontend (Vite)" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Both servers launched!
echo Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo Frontend: http://127.0.0.1:5173
echo.
pause
