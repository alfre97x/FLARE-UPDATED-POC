@echo off
echo Starting Python server for SpaceData Purchase application...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in the PATH. Please install Python 3.6 or higher.
    goto :end
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not installed or not in the PATH. Please install pip.
    goto :end
)

REM Check if requirements are installed
echo Checking and installing required packages...
pip install -r python_backend/requirements.txt

REM Start the Python server
echo Starting Python server on port 3000...
start cmd /k "python python_backend/app.py"

echo Server started successfully!
echo.
echo Access the application at: http://localhost:3000
echo API available at: http://localhost:3000/api
echo.
echo Press any key to exit this window...
pause > nul

:end
