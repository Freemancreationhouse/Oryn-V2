@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ORYN Studio V2 - FIX4
echo [FIX4] Corrected Windows launcher selected.
call "%~dp0RUN_ORYN_FIX4_WINDOWS.cmd"
echo [FIX4] Launcher finished. This terminal will remain open.
cmd.exe /k
