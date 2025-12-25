@echo off
chcp 65001 >nul 2>&1
REM TestCase Generator Script (Demo Version) for Windows

setlocal enabledelayedexpansion

REM Check arguments
if "%~1"=="" (
    echo Usage: %0 ^<file or directory path^>
    exit /b 1
)

set "TARGET=%~1"

REM Check if path exists
if not exist "%TARGET%" (
    echo Error: Path does not exist: %TARGET%
    exit /b 1
)

REM Check if it's a file
if exist "%TARGET%\" goto IS_DIR
if exist "%TARGET%" (
    echo Processing file: %TARGET%
    call :process_file "%TARGET%"
    echo Done!
    exit /b 0
)

:IS_DIR
REM If it's a directory
echo Processing directory: %TARGET%
set count=0

for /r "%TARGET%" %%f in (*) do (
    set "filename=%%~nxf"
    REM Skip if already a test file
    echo !filename! | findstr /C:"-test." >nul
    if errorlevel 1 (
        call :process_file "%%f"
        set /a count+=1
    )
)

echo Done! Processed !count! files
exit /b 0

:process_file
set "filepath=%~1"
set "dir=%~dp1"
set "filename=%~nx1"
set "name=%~n1"
set "ext=%~x1"

REM Generate test file name
if "%ext%"=="" (
    set "testfile=%dir%%name%-test"
) else (
    set "testfile=%dir%%name%-test%ext%"
)

REM Copy file as test case
copy "%filepath%" "%testfile%" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Failed to generate: %testfile%
) else (
    echo [OK] Generated: %testfile%
)
exit /b 0
