@echo off
title QS Marketplace
color 0A
cls

echo.
echo  =====================================================
echo   QS MARKETPLACE — Starting up...
echo  =====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please download and install Python from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, tick the box that says
    echo  "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] %PYVER% found.

REM Upgrade pip silently first
echo  [..] Updating pip...
python -m pip install --upgrade pip --quiet --disable-pip-version-check 2>nul

REM Install dependencies one by one so a single failure doesn't block everything
echo  [..] Installing dependencies (this may take a minute on first run)...

python -m pip install flask --quiet --disable-pip-version-check
python -m pip install flask-login --quiet --disable-pip-version-check
python -m pip install flask-sqlalchemy --quiet --disable-pip-version-check
python -m pip install flask-wtf --quiet --disable-pip-version-check
python -m pip install wtforms --quiet --disable-pip-version-check
python -m pip install sqlalchemy --quiet --disable-pip-version-check
python -m pip install email-validator --quiet --disable-pip-version-check

echo  [OK] Dependencies ready.
echo.
echo  =====================================================
echo   Starting server at http://127.0.0.1:5000
echo   Browser will open automatically in a few seconds.
echo.
echo   ADMIN LOGIN:
echo   Email   : admin@qsmarket.com
echo   Password: Admin@123
echo.
echo   Press CTRL+C to stop the server.
echo  =====================================================
echo.

python app.py

pause
