@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==========================================
echo   Inbox Archeology - Windows Launcher
echo ==========================================
echo.

REM Validate expected project files
if not exist "app.py" (
    echo ERROR: app.py not found in this folder.
    echo Run this script from the Inbox-Archeology project root.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found.
    pause
    exit /b 1
)

REM Find Python launcher
set "PY_EXE="
where py >nul 2>nul
if not errorlevel 1 set "PY_EXE=py -3"

if not defined PY_EXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_EXE=python"
)

if not defined PY_EXE (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.10+ and make sure PATH is configured.
    pause
    exit /b 1
)

REM Create venv if missing
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_EXE% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate venv
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

set "VENV_PY=.venv\Scripts\python.exe"

echo Upgrading pip...
%VENV_PY% -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

echo Installing requirements from requirements.txt...
%VENV_PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.txt.
    pause
    exit /b 1
)

REM Make sure expected folders exist
if not exist "input" mkdir input
if not exist "workspaces" mkdir workspaces

echo.
echo Launching Inbox Archeology...
echo.
echo App URL:
echo   http://127.0.0.1:8501
echo.
echo For real Gmail exports:
echo   1. Copy your .mbox file into the input\ folder
echo   2. Click "Refresh list" in the app
echo.

%VENV_PY% -m streamlit run app.py

echo.
echo Streamlit has stopped.
pause
endlocal