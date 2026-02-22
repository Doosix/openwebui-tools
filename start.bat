@echo off
echo ============================================
echo   OpenWebUI Multi-Tool Server
echo   Starting on http://localhost:8765
echo   Docs: http://localhost:8765/docs
echo ============================================
cd /d "%~dp0"
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8765 --reload
pause
