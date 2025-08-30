@echo off
echo Preparing SpaceData Purchase project for GitHub...

:: Create a new directory for the GitHub repository
set "github_dir=SpaceDataPurchase-GitHub"
if exist "%github_dir%" (
    echo Directory %github_dir% already exists. Removing...
    rmdir /s /q "%github_dir%"
)
mkdir "%github_dir%"

:: Copy essential files and directories

:: Core Python backend
mkdir "%github_dir%\python_backend"
mkdir "%github_dir%\python_backend\static"
mkdir "%github_dir%\python_backend\static\css"
mkdir "%github_dir%\python_backend\static\js"
mkdir "%github_dir%\python_backend\templates"

:: Copy Python backend files
copy "python_backend\app.py" "%github_dir%\python_backend\"
copy "python_backend\blockchain_api.py" "%github_dir%\python_backend\"
copy "python_backend\blockchain_bridge.py" "%github_dir%\python_backend\"
copy "python_backend\copernicus_api.py" "%github_dir%\python_backend\"
copy "python_backend\ai_service.py" "%github_dir%\python_backend\"
copy "python_backend\requirements.txt" "%github_dir%\python_backend\"
copy "python_backend\README.md" "%github_dir%\python_backend\"

:: Copy static files
copy "python_backend\static\css\*.css" "%github_dir%\python_backend\static\css\"
copy "python_backend\static\js\*.js" "%github_dir%\python_backend\static\js\"
copy "python_backend\static\placeholder.jpg" "%github_dir%\python_backend\static\"

:: Copy templates
copy "python_backend\templates\*.html" "%github_dir%\python_backend\templates\"

:: Smart contracts and ABIs
mkdir "%github_dir%\contracts"
mkdir "%github_dir%\abi"

copy "contracts\DataPurchase.sol" "%github_dir%\contracts\"
copy "contracts\DataPurchaseRandomizer.sol" "%github_dir%\contracts\"
copy "abi\datapurchase_abi.json" "%github_dir%\abi\"
copy "abi\datapurchase_randomizer_abi.json" "%github_dir%\abi\"
copy "abi\fdc_hub_abi.json" "%github_dir%\abi\"
copy "abi\fdc_verification_abi.json" "%github_dir%\abi\"
copy "abi\README.md" "%github_dir%\abi\"

:: Scripts
mkdir "%github_dir%\scripts"
copy "scripts\request_attestation.py" "%github_dir%\scripts\"
copy "scripts\oracle_manager.py" "%github_dir%\scripts\"
copy "scripts\README.md" "%github_dir%\scripts\"

:: Web app
mkdir "%github_dir%\web-app"
copy "web-app\index.html" "%github_dir%\web-app\"
copy "web-app\data-selection.html" "%github_dir%\web-app\"
copy "web-app\data-results.html" "%github_dir%\web-app\"
copy "web-app\styles.css" "%github_dir%\web-app\"
copy "web-app\wallet.js" "%github_dir%\web-app\"
copy "web-app\flare-services.js" "%github_dir%\web-app\"
copy "web-app\flare-vrf.js" "%github_dir%\web-app\"
copy "web-app\pricing.js" "%github_dir%\web-app\"
copy "web-app\copernicus-api.js" "%github_dir%\web-app\"
copy "web-app\metamask-connection.js" "%github_dir%\web-app\"

:: Configuration and documentation
copy "hardhat.config.js" "%github_dir%\"
copy "start-python-server.bat" "%github_dir%\"
copy "start-python-server.sh" "%github_dir%\"
copy "test-integration.py" "%github_dir%\"
copy "test-integration.bat" "%github_dir%\"
copy "test-integration.sh" "%github_dir%\"
copy "GITHUB_README.md" "%github_dir%\README.md"
copy "BLOCKCHAIN_INTEGRATION.md" "%github_dir%\"
copy ".gitignore" "%github_dir%\"
copy ".env.example" "%github_dir%\"

echo Files copied successfully.
echo.
echo Now sanitizing sensitive information...

:: Create a placeholder .env file
echo # This is an example .env file. Please fill in your own values. > "%github_dir%\.env.example"
echo # See .env.example for required variables >> "%github_dir%\.env.example"
type ".env.example" >> "%github_dir%\.env.example"

echo.
echo GitHub repository preparation complete!
echo The prepared files are in the %github_dir% directory.
echo.
echo Next steps:
echo 1. Review the files in %github_dir% to ensure no sensitive information remains
echo 2. Initialize a Git repository in the %github_dir% directory
echo 3. Add and commit the files
echo 4. Push to GitHub
echo.
pause
