@echo off
REM Ollama Vision Model Auto-Installer
REM Detects GPU VRAM and installs optimal model

echo ================================================
echo OLLAMA VISION MODEL AUTO-INSTALLER
echo ================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Ollama nicht gefunden!
    echo Bitte Ollama installieren: https://ollama.com
    pause
    exit /b 1
)

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python nicht gefunden!
    pause
    exit /b 1
)

echo [1/5] Erkenne GPU und VRAM...
echo.

REM Run GPU detection
python -c "import sys; sys.path.insert(0, 'backend'); from utils.gpu_detector import print_gpu_info; info = print_gpu_info(); print(f'RECOMMENDED_MODEL={info[\"recommended_vision_model\"]}'); print(f'VRAM={info[\"vram_gb\"]:.1f}')" > gpu_info.tmp

REM Parse recommended model
for /f "tokens=2 delims==" %%a in ('findstr "RECOMMENDED_MODEL" gpu_info.tmp') do set MODEL=%%a
for /f "tokens=2 delims==" %%a in ('findstr "VRAM" gpu_info.tmp') do set VRAM=%%a

REM Display detected info
type gpu_info.tmp
del gpu_info.tmp

echo.
echo ================================================
echo EMPFEHLUNG: %MODEL%
echo VRAM: %VRAM% GB
echo ================================================
echo.

REM Ask user for confirmation
echo Moechtest du %MODEL% installieren? (J/N)
set /p CONFIRM=
if /i not "%CONFIRM%"=="J" (
    echo Abgebrochen.
    pause
    exit /b 0
)

echo.
echo [2/5] Stoppe Ollama...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [3/5] Installiere %MODEL%...
echo Dies kann einige Minuten dauern...
ollama pull %MODEL%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Model download fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo [4/5] Starte Ollama...
start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
timeout /t 3 /nobreak >nul

echo.
echo [5/5] Teste Model...
ollama list | findstr "%MODEL%" >nul
if %ERRORLEVEL% EQU 0 (
    echo OK: %MODEL% ist installiert!
) else (
    echo WARNUNG: %MODEL% nicht in Liste!
)

echo.
echo ================================================
echo FERTIG!
echo ================================================
echo.
echo INFO:
echo Die Pipeline nutzt jetzt automatisch %MODEL%
echo Keine manuelle .env Aenderung noetig!
echo.
echo GPU Auto-Detection ist aktiv:
echo - 20+ GB VRAM = llava:34b (beste Qualitaet)
echo - 12-20 GB VRAM = llava:latest (hohe Qualitaet)
echo - 8-12 GB VRAM = llava:latest (standard)
echo - 4-8 GB VRAM = llava:7b (optimiert)
echo - weniger 4 GB = llava:7b (minimal)
echo.
echo Starte Pipeline neu:
echo   cd backend\tests
echo   python krai_master_pipeline.py
echo   Option 9
echo.
echo ================================================
echo.
pause
