#!/bin/bash
echo "Starting all servers for SpaceData Purchase application..."

# Start the Python server in a new terminal window
# For Mac
if [[ "$OSTYPE" == "darwin"* ]]; then
  osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && echo Starting Python server on port 3000... && python python_backend/app.py"'
# For Linux
else
  gnome-terminal -- bash -c "cd \"$(pwd)\" && echo Starting Python server on port 3000... && python python_backend/app.py; exec bash" || \
  xterm -e "cd \"$(pwd)\" && echo Starting Python server on port 3000... && python python_backend/app.py; exec bash" || \
  konsole -e "cd \"$(pwd)\" && echo Starting Python server on port 3000... && python python_backend/app.py; exec bash" || \
  echo "Could not open a new terminal window. Please run the Python server manually."
fi

# Wait a moment to ensure the Python server starts first
sleep 2

# Start the Node.js server in a new terminal window
# For Mac
if [[ "$OSTYPE" == "darwin"* ]]; then
  osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && echo Starting Node.js server on port 3001... && node server.js"'
# For Linux
else
  gnome-terminal -- bash -c "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  xterm -e "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  konsole -e "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  echo "Could not open a new terminal window. Please run the Node.js server manually."
fi

echo "All servers started successfully!"
echo ""
echo "Access the UI application at: http://localhost:3000"
echo "Access the blockchain API at: http://localhost:3001/web-app/"
echo ""
echo "Press Ctrl+C to exit this window..."
