#!/bin/bash
echo "SpaceData Purchase GitHub Preparation and Push Script"
echo "===================================================="
echo ""

echo "Step 1: Creating a backup of the current project..."
chmod +x backup-project.sh
./backup-project.sh
echo ""

echo "Step 2: Preparing files for GitHub..."
chmod +x prepare-for-github.sh
./prepare-for-github.sh
echo ""

echo "Step 3: Pushing to GitHub..."
chmod +x push-to-github.sh
./push-to-github.sh
echo ""

echo "All steps completed!"
echo ""
echo "Summary:"
echo "1. A backup of your project has been created in the parent directory"
echo "2. A clean version of your project has been prepared in SpaceDataPurchase-GitHub"
echo "3. The clean version has been pushed to GitHub at https://github.com/alfre97x/hackaton-flare-april.git"
echo ""
echo "If any step failed, you can run the individual scripts manually."
echo ""
read -p "Press Enter to continue..."

# Make this script executable with: chmod +x prepare-and-push-to-github.sh
