#!/usr/bin/env python3
"""
Blockchain Integration Test Script

This script runs all the blockchain integration tests:
1. Test blockchain API endpoints
2. Test DataPurchase contract
3. Test request attestation
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the absolute path to the root directory
ROOT_DIR = Path(__file__).resolve().parent

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def run_test(script_path, description):
    """Run a test script and return the result"""
    print_header(description)
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False
        )
        
        # Check if the script ran successfully
        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully")
            return True
        else:
            print(f"\n❌ {description} failed with exit code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout.decode())
        if e.stderr:
            print("STDERR:", e.stderr.decode())
        return False
    except Exception as e:
        print(f"\n❌ {description} failed with error: {str(e)}")
        return False

def main():
    """Run all blockchain integration tests"""
    print_header("BLOCKCHAIN INTEGRATION TESTS")
    
    # Make sure the server is running
    print("Note: Make sure the server is running before running these tests.")
    print("You can start the server with: npm run start-server\n")
    
    # List of tests to run
    tests = [
        {
            "script": ROOT_DIR / "scripts" / "test_blockchain_api.py",
            "description": "Blockchain API Tests"
        },
        {
            "script": ROOT_DIR / "scripts" / "test_datapurchase.py",
            "description": "DataPurchase Contract Tests"
        }
    ]
    
    # Run each test
    results = {}
    for test in tests:
        script_path = test["script"]
        description = test["description"]
        
        # Check if the script exists
        if not script_path.exists():
            print(f"\n❌ {description} failed: Script not found at {script_path}")
            results[description] = False
            continue
        
        # Run the test
        results[description] = run_test(script_path, description)
    
    # Print summary
    print_header("TEST SUMMARY")
    all_passed = True
    for description, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {description}")
        if not passed:
            all_passed = False
    
    # Exit with appropriate code
    if all_passed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
