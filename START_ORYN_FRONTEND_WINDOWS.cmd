@echo off
setlocal EnableExtensions
cd /d "%~dp0frontend"
set "NODE_EXE="
for /f "delims=" %%N in ('where node.exe 2^>nul') do if not defined NODE_EXE set "NODE_EXE=%%~fN"
if not defined NODE_EXE (
    echo [ERROR] Node.js was not found.
    goto :fail
)
set "NPM_CLI=%~dp0tools\npm-10.9.2\bin\npm-cli.js"
if not exist "%NPM_CLI%" (
    echo [ERROR] ORYN isolated npm is missing.
    goto :fail
)
"%NODE_EXE%" "%NPM_CLI%" run dev
if errorlevel 1 goto :fail
exit /b 0
:fail
echo [ERROR] ORYN frontend failed to start. No motion settings were changed.
pause
exit /b 1
