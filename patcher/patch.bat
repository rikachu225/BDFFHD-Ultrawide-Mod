@echo off
title BDFFHD Ultrawide Patcher
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found.
    echo   Install Python from https://www.python.org/downloads/
    echo   Make sure "Add to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)

:: Run patcher from script directory
cd /d "%~dp0"
python patch_ultrawide.py
