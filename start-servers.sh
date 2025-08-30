#!/bin/bash
echo "Starting server for SpaceData Purchase application..."

# Start the Node.js server in a new terminal window
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && echo Starting Node.js server on port 3001... && node server.js"'
else
  # Linux
  gnome-terminal -- bash -c "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  xterm -e "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  konsole -e "cd \"$(pwd)\" && echo Starting Node.js server on port 3001... && node server.js; exec bash" || \
  echo "Could not open a new terminal window. Please start the Node.js server manually with: node server.js"
fi

echo "Server started successfully!"
echo ""
echo "Access the application at: http://localhost:3001/web-app/"
echo ""
echo "Press Enter to exit this window..."
read
