@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo ORYN Studio V2 - CP2E Offline Safety Tests
echo No motor commands, COM ports or firmware writes.
echo ===============================================
call "scripts\select_oryn_python_for_tools.cmd"
if errorlevel 1 goto :fail
"%ORYN_PYTHON_EXE%" "scripts\cp2e_pattern_cleaning_selftest.py"
if errorlevel 1 goto :fail
"%ORYN_PYTHON_EXE%" -m pytest -q "tests\motion_contract"
if errorlevel 1 goto :fail
echo.
echo CP2E OFFLINE TESTS PASSED. Physical tests NOT CERTIFIED.
echo Report: CP2E_OFFLINE_MOTION_REPORT.txt
pause
exit /b 0
:fail
echo CP2E OFFLINE TESTS FAILED OR REQUIRED PYTHON PACKAGES ARE MISSING.
echo Run run_kinetiq_windows.bat first. If pytest is missing, install pytest into the ORYN .venv.
pause
exit /b 1
