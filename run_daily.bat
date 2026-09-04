@echo off
cd /d "%~dp0"

echo =====================================================
echo    ANIME STUDIO — UNATTENDED DAILY AUTOMATION RUN
echo =====================================================

if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe!
    exit /b 1
)

:: Include local FFmpeg binaries in PATH
if exist "%~dp0ffmpeg\bin" set "PATH=%~dp0ffmpeg\bin;%PATH%"

:: Activate virtualenv
call .venv\Scripts\activate.bat

:: Execute daily runner
python -u daily_runner.py %* >> daily_runner.log 2>&1
set RUN_EXIT_CODE=%ERRORLEVEL%

if %RUN_EXIT_CODE% EQU 0 (
    echo [Daily Bat] Run succeeded.
) else (
    echo [Daily Bat] Run failed with error code %RUN_EXIT_CODE%.
)

exit /b %RUN_EXIT_CODE%
