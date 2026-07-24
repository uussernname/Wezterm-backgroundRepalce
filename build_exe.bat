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
echo [3/3] Preparing release folder ...
if exist "release" rmdir /s /q "release"
mkdir "release"
xcopy "dist\TraceOn\*" "release\" /E /Q >nul
copy "wezterm_template.lua" "release\" >nul
copy "add_to_path.bat" "release\" >nul
copy "README.md" "release\" >nul
echo   Release folder: release\
echo.
echo   ============================================
echo     How to distribute:
echo       Zip the "release" folder and share it.
echo.
echo     For the end user:
echo       1. Unzip to any folder
echo       2. Edit config.json (paths + image folder)
echo       3. Double-click add_to_path.bat
echo       4. Open new terminal, type "TraceOn"
echo   ============================================
echo.
pause
