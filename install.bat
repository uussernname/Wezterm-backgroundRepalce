@echo off
title TraceOn - Installer

echo Checking Python ...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8+ first:
    echo   https://www.python.org/downloads/
    echo.
    echo During installation, check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo Python found. Starting installer ...
echo.

python install.py

if %errorlevel% neq 0 (
    echo.
    echo Installer exited with an error.
    pause
    exit /b 1
)

echo.
echo All done! Press any key to close.
pause >nul
