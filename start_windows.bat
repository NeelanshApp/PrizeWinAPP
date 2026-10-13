@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup_windows.bat first.
    pause
    exit /b 1
)
echo Keep this window open. Press Ctrl+C to stop the app.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost
if errorlevel 1 pause
