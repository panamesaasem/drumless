@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Run setup_windows.bat first.
    pause
    exit /b 1
)

if "%~1"=="" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0drumless.py" --pick
) else (
    "%~dp0.venv\Scripts\python.exe" "%~dp0drumless.py" "%~1"
)
set "result=%errorlevel%"
echo.
pause
exit /b %result%
