@echo off
echo ============================================================
echo Applying Migration 82: Cleanup duplicate views and rules
echo ============================================================
echo.

cd /d "%~dp0"

REM Load environment variables
for /f "tokens=*" %%a in ('type .env.database') do set %%a

REM Apply migration
psql "%DATABASE_URL%" -f "database/migrations/82_cleanup_duplicate_views_and_rules.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo Migration 82 applied successfully!
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo ERROR: Migration 82 failed!
    echo ============================================================
)

pause
