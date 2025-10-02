@echo off
REM Ollama GPU Fix - Kleineres Model installieren
REM Fixes: "model runner has unexpectedly stopped" errors

echo ================================================
echo OLLAMA GPU FIX - Kleineres Vision Model
echo ================================================
echo.
echo Dein System: 8GB VRAM GPU
echo Aktuelles Problem: llava:latest (11GB) zu gross
echo Loesung: llava:7b (4GB) installieren
echo.
echo ================================================

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Ollama nicht gefunden!
    echo Bitte Ollama installieren: https://ollama.com
    pause
    exit /b 1
)

echo.
echo [1/4] Stoppe Ollama...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/4] Installiere llava:7b (4GB Model)...
echo Dies kann einige Minuten dauern...
ollama pull llava:7b

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Model download fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo [3/4] Starte Ollama...
start "" "C:\Users\haast\AppData\Local\Programs\Ollama\ollama.exe" serve
timeout /t 3 /nobreak >nul

echo.
echo [4/4] Teste Model...
echo Teste ob llava:7b funktioniert...
ollama list | findstr "llava:7b" >nul
if %ERRORLEVEL% EQU 0 (
    echo OK: llava:7b ist installiert!
) else (
    echo WARNUNG: llava:7b nicht in Liste!
)

echo.
echo ================================================
echo FERTIG!
echo ================================================
echo.
echo Naechste Schritte:
echo 1. Pruefe deine .env Datei:
echo    OLLAMA_MODEL_VISION=llava:7b
echo.
echo 2. Starte die Pipeline neu
echo    cd backend\tests
echo    python krai_master_pipeline.py
echo.
echo 3. Waehle Option 9
echo.
echo ================================================
echo.
pause
