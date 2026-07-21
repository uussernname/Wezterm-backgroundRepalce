@echo off
echo ========================================
echo   TraceOn - Setup Virtual Environment
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python first.
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Creating virtual environment...
if exist "venv" (
    echo   venv already exists, skipping.
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo   venv created.
)

echo [2/2] Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install pyinstaller

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup complete!
echo   Run build_exe.bat to build TraceOn.exe
echo ========================================
pause
