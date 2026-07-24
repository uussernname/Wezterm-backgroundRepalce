@echo off
title TraceOn - Setup

echo ========================================
echo   TraceOn - One-time Setup
echo ========================================
echo.

REM Step 1: Unblock files blocked by SmartScreen
echo [1/2] Removing Windows block from downloaded files ...
powershell -Command "Get-ChildItem -Path '%~dp0' -Recurse | Unblock-File" >nul 2>&1
echo   Done.
echo.

REM Step 2: Add to PATH
echo [2/2] Adding to PATH ...
echo.
echo   This lets you type "TraceOn" from any terminal.
echo.
set /p confirm="  Continue? [Y/n]: "
if /i not "%confirm%"=="Y" if /i not "%confirm%"=="" exit /b

set "THIS_DIR=%~dp0"
set "THIS_DIR=%THIS_DIR:~0,-1%"

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURPATH=%%b"
if not defined CURPATH set "CURPATH="

echo %CURPATH%; | findstr /i /c:"%THIS_DIR%"; >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Already in PATH.
    pause >nul
    exit /b
)

setx PATH "%CURPATH%;%THIS_DIR%"

echo.
echo Done! Open a NEW terminal and type:
echo   TraceOn
echo.
pause >nul
