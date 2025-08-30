#!/bin/bash

echo "==================================="
echo "Blockchain Integration Test Script"
echo "==================================="
echo

echo "Starting Python backend..."
cd python_backend && python app.py &
PYTHON_PID=$!
cd ..

echo "Waiting for server to start..."
sleep 5

echo
echo "==================================="
echo "Testing Python blockchain bridge..."
echo "==================================="
echo
cd python_backend
python test_blockchain_bridge.py
cd ..

echo
echo "==================================="
echo "Web interface test..."
echo "==================================="
echo
echo "Opening blockchain test page in default browser..."

# Try to open the browser in a platform-independent way
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:5000/blockchain-test.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:5000/blockchain-test.html 2>/dev/null || \
    sensible-browser http://localhost:5000/blockchain-test.html 2>/dev/null || \
    x-www-browser http://localhost:5000/blockchain-test.html 2>/dev/null || \
    gnome-open http://localhost:5000/blockchain-test.html 2>/dev/null
else
    # Other OS
    echo "Please open http://localhost:5000/blockchain-test.html in your browser"
fi

echo
echo "==================================="
echo "Test script completed!"
echo "==================================="
echo
echo "Please check the test results above and in the browser."
echo "Press Enter to exit and stop the server..."
read

# Kill the server process
kill $PYTHON_PID

echo "Server stopped."
