@echo off
echo Starting all servers for SpaceData Purchase application...

REM Start the Python server in a new terminal window
start cmd /k "echo Starting Python server on port 3000... && python python_backend/app.py"

REM Wait a moment to ensure the Python server starts first
timeout /t 2 /nobreak > nul

REM Start the Node.js server in a new terminal window
start cmd /k "echo Starting Node.js server on port 3001... && node server.js"

echo All servers started successfully!
echo.
echo Access the UI application at: http://localhost:3000
echo Access the blockchain API at: http://localhost:3001/web-app/
echo.
echo Press any key to exit this window...
pause > nul
