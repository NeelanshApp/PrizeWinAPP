@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto no_launcher
py -3.12 -m venv .venv
if not errorlevel 1 goto install
py -3.11 -m venv .venv
if not errorlevel 1 goto install
goto failed
:no_launcher
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" verify.py
if errorlevel 1 goto failed
echo Setup and all checks passed. Double-click start_windows.bat to use the app.
pause
exit /b 0
:failed
echo Setup or checks failed. Read the error above and verification.log if created. See README.md.
pause
exit /b 1
