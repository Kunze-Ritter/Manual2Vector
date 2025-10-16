@echo off
echo ========================================
echo OpenCV Installation
echo ========================================
echo.
echo Choose OpenCV version:
echo 1. CPU-only (Standard, einfach)
echo 2. GPU-enabled (CUDA required)
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Installing CPU-only OpenCV...
    pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
    pip install opencv-python
    echo.
    echo ========================================
    echo CPU-only OpenCV installed!
    echo ========================================
    echo.
    echo Add to .env:
    echo USE_GPU=false
    echo.
) else if "%choice%"=="2" (
    echo.
    echo Installing GPU-enabled OpenCV...
    echo WARNING: This requires CUDA and cuDNN to be installed!
    echo.
    pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
    pip install opencv-contrib-python
    echo.
    echo ========================================
    echo GPU-enabled OpenCV installed!
    echo ========================================
    echo.
    echo Add to .env:
    echo USE_GPU=true
    echo CUDA_VISIBLE_DEVICES=0
    echo.
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

pause
