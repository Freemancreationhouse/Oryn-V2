@echo off
setlocal
cd /d "%~dp0"
echo ORYN Magic Home RGB Wi-Fi Discovery - no motors or settings changes
call "scripts\select_oryn_python_for_tools.cmd"
if errorlevel 1 goto :fail
"%ORYN_PYTHON_EXE%" "scripts\discover_magic_home_rgb.py"
if errorlevel 1 goto :fail
pause
exit /b 0
:fail
echo Discovery startup failed. No lighting settings were changed.
pause
exit /b 1
