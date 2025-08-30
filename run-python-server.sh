#!/bin/bash
echo "Starting Python server for SpaceData Purchase application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed or not in the PATH. Please install Python 3.6 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip is not installed or not in the PATH. Please install pip."
    exit 1
fi

# Check if requirements are installed
echo "Checking and installing required packages..."
pip3 install -r python_backend/requirements.txt

# Start the Python server in a new terminal window
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && python3 python_backend/app.py"'
else
    # Linux
    gnome-terminal -- bash -c "cd \"$(pwd)\" && python3 python_backend/app.py; exec bash" || \
    xterm -e "cd \"$(pwd)\" && python3 python_backend/app.py; exec bash" || \
    konsole -e "cd \"$(pwd)\" && python3 python_backend/app.py; exec bash" || \
    echo "Could not open a new terminal window. Please start the Python server manually with: python3 python_backend/app.py"
fi

echo "Server started successfully!"
echo ""
echo "Access the application at: http://localhost:3000"
echo "API available at: http://localhost:3000/api"
echo ""
echo "Press Enter to exit this window..."
read
