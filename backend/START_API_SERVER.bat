@echo off
echo ========================================
echo STARTING KRAI BACKEND API SERVER
echo ========================================
echo.
echo Port: 8000
echo Docs: http://localhost:8000/docs
echo.

cd /d "%~dp0"

echo Checking for virtual environment...
if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found, using system Python
)

echo Starting FastAPI server...
python main.py

pause
