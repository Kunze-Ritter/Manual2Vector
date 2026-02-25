@echo off
:: Installiert fehlende LangChain / LangGraph Pakete in das Backend-venv
:: Einmalig ausführen, dann test_agent_local.py nutzen

echo ============================================================
echo  KRAI – Agent-Abhängigkeiten installieren (lokales venv)
echo ============================================================
echo.

set VENV_PIP=backend\venv\Scripts\pip.exe

if not exist %VENV_PIP% (
    echo FEHLER: venv nicht gefunden bei backend\venv\
    echo Bitte zuerst setup.ps1 ausführen.
    exit /b 1
)

echo Installiere LangChain 1.x + LangGraph...
%VENV_PIP% install ^
    "langchain>=1.0.0,<2.0.0" ^
    "langchain-core>=1.0.0,<2.0.0" ^
    "langchain-ollama>=1.0.0,<2.0.0" ^
    "langchain-community>=0.4.0,<2.0.0" ^
    "langgraph>=1.0.0,<2.0.0"

if %errorlevel% neq 0 (
    echo.
    echo FEHLER beim Installieren der Pakete!
    exit /b 1
)

echo.
echo ============================================================
echo  Installation abgeschlossen!
echo  Jetzt testen mit:
echo    backend\venv\Scripts\python.exe test_agent_local.py
echo ============================================================
