@echo off
title RAG System

echo Starting RAG Knowledge Base Q&A System...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the two popup windows to stop all services.
echo.

cd /D "%~dp0"

start "RAG-Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"
start "RAG-Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 >nul
start http://localhost:3000

echo All services started.
pause
