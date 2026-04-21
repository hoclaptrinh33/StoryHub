@echo off
cd /d "%~dp0backend"
"%~dp0.venv\Scripts\uvicorn.exe" app.main:app --reload --host 127.0.0.1 --port 8000
pause
