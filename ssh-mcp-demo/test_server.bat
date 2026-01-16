@echo off
echo ================================
echo Testing SSH MCP Server
echo ================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo Error: Virtual environment not found
    echo Please run setup_venv.bat first
    pause
    exit /b 1
)

echo Using Python from virtual environment...
venv\Scripts\python.exe --version
echo.

echo Testing server imports...
venv\Scripts\python.exe -c "import paramiko; import mcp; print('✓ All dependencies installed successfully')"

if errorlevel 1 (
    echo.
    echo Error: Dependencies not installed correctly
    echo Please run setup_venv.bat again
    pause
    exit /b 1
)

echo.
echo ================================
echo Test completed successfully!
echo ================================
echo.
echo Server is ready to use with Claude Code
echo.
pause
