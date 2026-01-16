@echo off
echo ================================
echo SSH MCP Server - Virtual Environment Setup
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

echo Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo.
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ================================
echo Setup completed successfully!
echo ================================
echo.
echo Virtual environment created at: %CD%\venv
echo.
echo Next steps:
echo 1. Copy config.json.example to config.json
echo    Command: copy config.json.example config.json
echo.
echo 2. Edit config.json with your SSH server details
echo.
echo 3. Configure Claude Code with the following settings:
echo.
echo    File: %%USERPROFILE%%\.claude\claude_code_config.json
echo.
echo    Content:
echo    {
echo      "mcpServers": {
echo        "ssh-server": {
echo          "command": "%CD%\venv\Scripts\python.exe",
echo          "args": ["%CD%\server.py"]
echo        }
echo      }
echo    }
echo.
echo 4. Reload Claude Code window
echo.
pause
