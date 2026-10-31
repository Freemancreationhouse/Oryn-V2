@echo off
setlocal
cd /d "%~dp0"
echo ===========================================================
echo ORYN STUDIO V2 - WINDOWS READ-ONLY PREVIEW
echo ===========================================================
echo Close previous ORYN Vite and backend windows first.
echo Keep the kinetic sand machine disconnected for preview.
echo.
call "scripts\select_oryn_python_for_tools.cmd"
if errorlevel 1 goto :fail
"%ORYN_PYTHON_EXE%" -u "scripts\start_v2_preview_windows.py"
if errorlevel 1 goto :fail
pause
exit /b 0
:fail
echo Preview failed. Check any preview_logs output.
pause
exit /b 1
