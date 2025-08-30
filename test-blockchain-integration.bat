@echo off
echo ===================================
echo Blockchain Integration Test Script
echo ===================================
echo.

echo Starting Python backend...
start cmd /k "cd python_backend && python app.py"

echo Waiting for server to start...
timeout /t 5 /nobreak > nul

echo.
echo ===================================
echo Testing Python blockchain bridge...
echo ===================================
echo.
cd python_backend
python test_blockchain_bridge.py
cd ..

echo.
echo ===================================
echo Web interface test...
echo ===================================
echo.
echo Opening blockchain test page in default browser...
start http://localhost:5000/blockchain-test.html

echo.
echo ===================================
echo Test script completed!
echo ===================================
echo.
echo Please check the test results above and in the browser.
echo Press any key to exit...
pause > nul
