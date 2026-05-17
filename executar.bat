@echo off
echo ============================================
echo   Digital Twin - Sprint 2
echo   Iniciando aplicacao...
echo ============================================
echo.

cd /d "%~dp0"

python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause
