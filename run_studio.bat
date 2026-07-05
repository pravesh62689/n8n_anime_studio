@echo off
cd /d "%~dp0"
echo =====================================================
echo       100%% LOCAL ANIME STUDIO — STARTING UP
echo =====================================================

if not exist .venv (
    echo [ERROR] Virtual environment missing! Run:
    echo         python -m venv .venv
    echo         .venv\Scripts\activate
    echo         pip install -r requirements.txt
    pause
    exit /b 1
)

:: Include local FFmpeg binaries in PATH
set PATH=%CD%\ffmpeg\bin;%PATH%

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Launch the standalone Python orchestrator
echo Starting Anime Studio Orchestrator (08:00 and 20:00 daily)...
echo.
python orchestrator.py

pause
