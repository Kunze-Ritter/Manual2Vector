@echo off
echo ========================================
echo KRAI AI Agent Installation
echo ========================================
echo.

echo Uninstalling old versions...
pip uninstall -y langchain langchain-community langchain-core psycopg2-binary 2>nul

echo.
echo Installing LangChain dependencies...
pip install "numpy>=2.1.0,<2.3.0"
pip install --upgrade langchain
pip install --upgrade langchain-community
pip install --upgrade langchain-core
pip install "psycopg[binary]"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To test the agent, run:
echo   python test_agent.py
echo.
echo To start the API, run:
echo   python app.py
echo.
echo The agent will be available at:
echo   http://localhost:8000/agent
echo.
pause
