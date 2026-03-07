@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==========================================
echo   Inbox Archeology - Windows Launcher
echo ==========================================
echo.

REM Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.11+ and make sure "Add Python to PATH" is enabled.
    pause
    exit /b 1
)

REM Create venv if missing
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
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

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip.
    pause
    exit /b 1
)

REM Install requirements if file exists
if exist "requirements.txt" (
    echo Installing requirements from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install requirements.txt.
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found.
)

REM Ensure python-dotenv is present
echo Ensuring python-dotenv is installed...
pip install python-dotenv
if errorlevel 1 (
    echo ERROR: Failed to install python-dotenv.
    pause
    exit /b 1
)

REM Make sure expected folders exist
if not exist "input" mkdir input
if not exist "workspaces" mkdir workspaces
if not exist "output" mkdir output
if not exist "steps" (
    echo WARNING: steps folder not found.
)

echo.
echo Launching Inbox Archeology...
echo.
echo When Streamlit opens, use:
echo   http://localhost:8501
echo.

streamlit run app.py

echo.
echo Streamlit has stopped.
pause
endlocal