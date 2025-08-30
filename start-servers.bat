@echo off
echo Starting server for SpaceData Purchase application...

REM Start the Node.js server in a new terminal window
start cmd /k "echo Starting Node.js server on port 3001... && node server.js"

echo Server started successfully!
echo.
echo Access the application at: http://localhost:3001/web-app/
echo.
echo Press any key to exit this window...
pause > nul
