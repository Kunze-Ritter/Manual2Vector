@echo off
REM Start Pipeline mit Performance Monitoring
REM Opens two windows: Performance Monitor + Pipeline

echo ================================================
echo KR-AI Pipeline mit Performance Monitoring
echo ================================================
echo.
echo Startet 2 Fenster:
echo 1. Performance Monitor (real-time)
echo 2. Master Pipeline (Option 9)
echo.
echo Druecke beliebige Taste zum Starten...
pause > nul

REM Start Performance Monitor in neuem Fenster
start "Performance Monitor" cmd /k "python performance_monitor.py --interval 1 --output performance_log.json"

REM Warte kurz damit Monitor startet
timeout /t 2 /nobreak > nul

REM Start Pipeline
echo.
echo Starte Pipeline...
echo Waehle Option 9 fuer Smart Processing mit Quality Check
echo.
python krai_master_pipeline.py

REM Warte am Ende
pause
