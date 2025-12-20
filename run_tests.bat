@echo off
REM Quick Test Runner for KRAI Integration Tests
REM Batch wrapper for PowerShell script

if "%1"=="" (
    powershell -ExecutionPolicy Bypass -File run_tests.ps1 help
) else (
    powershell -ExecutionPolicy Bypass -File run_tests.ps1 %1
)
