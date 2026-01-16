@echo off
echo ================================
echo SSH MCP Server - Installation
echo ================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ================================
echo Installation completed!
echo ================================
echo.
echo Next steps:
echo 1. Copy config.json.example to config.json
echo 2. Edit config.json with your SSH server details
echo 3. Configure Claude Code (see CLAUDE_CODE_SETUP.md)
echo.
pause
