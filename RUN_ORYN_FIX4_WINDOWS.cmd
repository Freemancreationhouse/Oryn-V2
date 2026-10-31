@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title ORYN Studio V2 - FIX4 SINGLE-WINDOW DIAGNOSTIC
color 0A
echo.
echo ============================================================
echo  ORYN STUDIO V2 - FIX4 - THIS IS THE NEW LAUNCHER
echo ============================================================
echo  New launcher name: RUN_ORYN_FIX4_WINDOWS.cmd
echo  Do not use the older run_kinetiq_windows.bat for this test.
echo.
set "PYTHON_EXE="
if not exist "scripts\select_healthy_python_windows.ps1" goto :missing
for /f "usebackq delims=" %%P in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\select_healthy_python_windows.ps1"`) do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE goto :missingpython
if not exist "scripts\oryn_fix4_supervisor.py" goto :missing
"%PYTHON_EXE%" -u "scripts\oryn_fix4_supervisor.py"
set "RESULT=%errorlevel%"
echo.
echo ============================================================
echo  FIX4 SUPERVISOR FINISHED (exit %RESULT%)
echo  If failed, send any errors above plus oryn\startup_logs\
echo  The window will remain open. Type exit to close it.
echo ============================================================
goto :keepopen
:missingpython
echo [FAIL] Could not locate a healthy Python 3.12 install.
goto :keepopen
:missing
echo [FAIL] FIX4 files or existing ORYN Python selector missing.
echo [FAIL] Extract Fix4 into the folder containing the oryn folder.
echo [FAIL] Expected: C:\ORYN WITH WIFI\oryn\scripts\...
:keepopen
cmd.exe /k
