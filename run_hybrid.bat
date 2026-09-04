@echo off
cd /d "%~dp0"
echo =====================================================
echo   HYBRID MODE: n8n + FastMCP Anime Studio
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

:: Launch the MCP Tool Server in a separate terminal window
echo Starting Python MCP Tool Server (port 8000)...
start "MCP - Anime Studio Tools" cmd /k ".venv\Scripts\python.exe studio_mcp.py"

:: Give the MCP server 3 seconds to bind its port before n8n connects
timeout /t 3 /nobreak >nul

:: Launch local n8n visual editor in a separate terminal window
echo Starting Local n8n Engine (port 5678)...
start "n8n Visual Orchestrator" cmd /k "npx n8n"

echo.
echo =====================================================
echo  SYSTEM ONLINE!
echo  MCP Tool Server : http://localhost:8000
echo  n8n Visual UI   : http://localhost:5678
echo.
echo  Import n8n_workflow_template.json into n8n to
echo  connect the visual pipeline to the MCP tools.
echo =====================================================
pause
