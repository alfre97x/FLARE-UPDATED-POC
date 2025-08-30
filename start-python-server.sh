#!/bin/bash
echo "Starting Python backend server..."
cd python_backend && python app.py &
echo "Python backend server started at http://localhost:5000"
