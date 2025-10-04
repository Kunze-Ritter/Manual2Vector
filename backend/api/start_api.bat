@echo off
echo.
echo ========================================
echo   KRAI Processing Pipeline API
echo ========================================
echo.

REM Activate virtual environment if exists
if exist "../../.venv/Scripts/activate.bat" (
    echo Activating virtual environment...
    call ../../.venv/Scripts/activate.bat
)

REM Check if FastAPI is installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: FastAPI not installed!
    echo.
    echo Installing requirements...
    pip install -r requirements.txt
)

echo.
echo Starting FastAPI server...
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.

python app.py

pause
