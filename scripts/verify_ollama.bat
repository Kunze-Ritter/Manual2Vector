@echo off
REM Ollama Status Verification Script
REM Checks if Ollama is running correctly with llava:7b

REM Change to script directory
cd /d "%~dp0"

REM Set UTF-8 encoding for emoji support
chcp 65001 >nul 2>&1

echo ================================================
echo OLLAMA STATUS VERIFICATION
echo ================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ollama ist nicht installiert!
    echo Bitte installieren: https://ollama.com
    pause
    exit /b 1
)

echo [1/4] Ollama Installation: OK
echo.

REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if %ERRORLEVEL% EQU 0 (
    echo [2/4] Ollama Service: RUNNING
) else (
    echo [2/4] Ollama Service: NOT RUNNING
    echo         Starting Ollama...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >nul
)
echo.

REM Check if llava:7b is installed
echo [3/4] Checking installed models...
ollama list | findstr "llava" >nul
if %ERRORLEVEL% EQU 0 (
    echo         llava models found:
    ollama list | findstr "llava"
) else (
    echo         [WARNING] No llava models installed!
    echo         Run: ollama pull llava:7b
)
echo.

REM Test Ollama API
echo [4/4] Testing Ollama API...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo         API Response: OK
) else (
    echo         [ERROR] API not responding!
    echo         Is Ollama running?
)
echo.

REM Show GPU info
echo ================================================
echo GPU INFORMATION
echo ================================================
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -c "import sys; sys.path.insert(0, 'backend'); from utils.gpu_detector import print_gpu_info; print_gpu_info()"
) else (
    echo Python not found - skipping GPU detection
)

echo.
echo ================================================
echo RECOMMENDATIONS
echo ================================================
echo.
echo If llava:7b is NOT installed:
echo   Run: ollama pull llava:7b
echo.
echo If Ollama keeps crashing:
echo   1. Stop Ollama: taskkill /F /IM ollama.exe
echo   2. Run: fix_ollama_gpu.bat
echo   3. Restart the pipeline
echo.
echo ================================================
pause
