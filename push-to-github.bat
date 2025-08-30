@echo off
echo Pushing SpaceData Purchase project to GitHub...

set "github_dir=SpaceDataPurchase-GitHub"
set "github_repo=https://github.com/alfre97x/hackaton-flare-april.git"

if not exist "%github_dir%" (
    echo Error: Directory %github_dir% does not exist.
    echo Please run prepare-for-github.bat first.
    pause
    exit /b 1
)

cd "%github_dir%"

echo Initializing Git repository...
git init

echo Adding all files to Git...
git add .

echo Committing files...
git commit -m "Initial commit of SpaceData Purchase project"

echo Setting remote repository...
git remote add origin %github_repo%

echo Pushing to GitHub...
git push -u origin master

if %ERRORLEVEL% neq 0 (
    echo.
    echo Note: If you encountered an authentication error, you may need to:
    echo 1. Create a personal access token on GitHub
    echo 2. Use the token as your password when prompted
    echo.
    echo You can also try:
    echo git push -u origin master
    echo.
    echo from within the %github_dir% directory.
)

echo.
echo Process completed. Please check the output for any errors.
cd ..
pause
