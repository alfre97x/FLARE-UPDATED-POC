@echo off
echo SpaceData Purchase GitHub Preparation and Push Script
echo ====================================================
echo.

echo Step 1: Creating a backup of the current project...
call backup-project.bat
echo.

echo Step 2: Preparing files for GitHub...
call prepare-for-github.bat
echo.

echo Step 3: Pushing to GitHub...
call push-to-github.bat
echo.

echo All steps completed!
echo.
echo Summary:
echo 1. A backup of your project has been created in the parent directory
echo 2. A clean version of your project has been prepared in SpaceDataPurchase-GitHub
echo 3. The clean version has been pushed to GitHub at https://github.com/alfre97x/hackaton-flare-april.git
echo.
echo If any step failed, you can run the individual scripts manually.
echo.
pause
