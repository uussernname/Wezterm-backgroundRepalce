@echo off
echo ========================================
echo   TraceOn - Build EXE
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Run setup.bat first.
    pause
    exit /b 1
)

echo [1/2] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec" 2>nul

echo [2/2] Building TraceOn (--onedir mode) ...
venv\Scripts\python.exe -m PyInstaller --onedir --name TraceOn --clean TraceOn.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo   Output: dist\TraceOn\
echo ========================================
echo.
echo   How to use:
echo     1. Copy the entire dist\TraceOn\ folder
echo        to e.g. D:\Tools\TraceOn\
echo     2. Add D:\Tools\TraceOn to system PATH
echo        (NOT the .exe file, but the FOLDER)
echo     3. Run "TraceOn" in any terminal
echo.
echo   config.json will be auto-generated
echo   inside the TraceOn folder on first run.
echo.
pause
