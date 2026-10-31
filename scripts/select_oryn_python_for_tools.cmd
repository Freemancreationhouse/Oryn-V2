@echo off
rem Sets ORYN_PYTHON_EXE in caller's environment. Call this script, do not run directly.
set "ORYN_PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -I -c "import sys,ssl;assert (3,11) <= sys.version_info[:2] <= (3,13)" >nul 2>nul
    if not errorlevel 1 set "ORYN_PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
)
if not defined ORYN_PYTHON_EXE (
    for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\select_healthy_python_windows.ps1"`) do set "ORYN_PYTHON_EXE=%%P"
)
if not defined ORYN_PYTHON_EXE (
    echo [ERROR] A healthy Python 3.12 environment is required. Run run_kinetiq_windows.bat first.
    exit /b 1
)
exit /b 0
