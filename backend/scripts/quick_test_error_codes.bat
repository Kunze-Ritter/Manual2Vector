@echo off
REM Quick Test Script for Error Code Extraction
REM Usage: quick_test_error_codes.bat [path_to_pdf]

echo.
echo ========================================
echo Error Code Extraction Quick Test
echo ========================================
echo.

if "%1"=="" (
    echo Usage: quick_test_error_codes.bat [path_to_pdf]
    echo.
    echo Example:
    echo   quick_test_error_codes.bat "C:\Manuals\bizhub_4750i_SM.pdf"
    echo.
    pause
    exit /b 1
)

set PDF_PATH=%~1
set OUTPUT_FILE=quick_test_result_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set OUTPUT_FILE=%OUTPUT_FILE: =0%

echo Testing: %PDF_PATH%
echo Output:  %OUTPUT_FILE%
echo.

cd /d "%~dp0.."
python scripts/test_error_code_extraction.py --pdf "%PDF_PATH%" --output "%OUTPUT_FILE%"

if errorlevel 1 (
    echo.
    echo [ERROR] Test failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Report saved to: %OUTPUT_FILE%
echo.

REM Open report
if exist "%OUTPUT_FILE%" (
    echo Opening report...
    start notepad "%OUTPUT_FILE%"
)

pause
