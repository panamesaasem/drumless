@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found. Install Python 3.12 x64 first.
    goto :fail
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo FFmpeg was not found on PATH. Install it and reopen this window.
    goto :fail
)
where ffprobe >nul 2>nul
if errorlevel 1 (
    echo ffprobe was not found on PATH. Install FFmpeg and reopen this window.
    goto :fail
)

py -3.12 -m venv "%~dp0.venv"
if errorlevel 1 goto :fail
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :fail

echo.
echo Setup complete. Drag an audio file onto run_windows.bat.
pause
exit /b 0

:fail
echo.
echo Setup failed. See README.md for Windows instructions.
pause
exit /b 1
