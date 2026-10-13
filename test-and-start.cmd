@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup_windows.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" verify.py
if errorlevel 1 goto failed
call start_windows.bat
exit /b %errorlevel%
:failed
echo Checks failed. The app was not launched. Read verification.log for details.
pause
exit /b 1
