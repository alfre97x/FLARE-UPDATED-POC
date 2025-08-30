# How to Run the GitHub Preparation Scripts

This document provides instructions on how to run the scripts we've created to prepare your project for GitHub.

## Windows Instructions

To run the scripts on Windows, you need to use the Command Prompt or PowerShell. Here's how to run each script:

### Individual Scripts

1. **Create a backup**:
   ```
   .\backup-project.bat
   ```

2. **Prepare files for GitHub**:
   ```
   .\prepare-for-github.bat
   ```

3. **Push to GitHub**:
   ```
   .\push-to-github.bat
   ```

### All-in-One Script

To run all steps in sequence:
```
.\prepare-and-push-to-github.bat
```

## Linux/macOS Instructions

To run the scripts on Linux or macOS, you need to use the Terminal. First, make the scripts executable:

```
chmod +x *.sh
```

Then you can run each script:

### Individual Scripts

1. **Create a backup**:
   ```
   ./backup-project.sh
   ```

2. **Prepare files for GitHub**:
   ```
   ./prepare-for-github.sh
   ```

3. **Push to GitHub**:
   ```
   ./push-to-github.sh
   ```

### All-in-One Script

To run all steps in sequence:
```
./prepare-and-push-to-github.sh
```

## Common Issues

### "Command not found" or "is not recognized as an internal or external command"

This error occurs when:
- You're not in the correct directory
- You typed the filename incorrectly
- You're using the wrong slash (use `.\` for Windows, `./` for Linux/macOS)

Make sure you're in the project root directory (`c:/Users/alfre/Desktop/CODING/SpaceDataPurchase`) and type the command exactly as shown above.

### "Permission denied"

On Linux/macOS, you might need to make the scripts executable first:
```
chmod +x *.sh
```

### "The system cannot find the path specified"

This error occurs when the script tries to access a file or directory that doesn't exist. Make sure all the required files are in the correct locations.

## What Each Script Does

- **backup-project**: Creates a backup of your entire project in the parent directory
- **prepare-for-github**: Copies only the essential files to a new directory, removing sensitive information
- **push-to-github**: Initializes a Git repository and pushes it to GitHub
- **prepare-and-push-to-github**: Runs all the steps in sequence

## Next Steps

After running these scripts:

1. Check the `SpaceDataPurchase-GitHub` directory to ensure it contains all the necessary files
2. Verify that no sensitive information is included
3. If everything looks good, the files should be pushed to GitHub at https://github.com/alfre97x/hackaton-flare-april.git
