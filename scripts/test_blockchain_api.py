#!/usr/bin/env python3
"""
Test script for blockchain API endpoints

This script tests the blockchain API endpoints we've implemented:
- /api/blockchain/config
- /api/blockchain/verify
- /api/blockchain/purchase
"""

import os
import json
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Get the absolute path to the root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the root directory
DOTENV_PATH = ROOT_DIR / '.env'
load_dotenv(DOTENV_PATH)

# Base URL for API requests
API_BASE_URL = 'http://localhost:3001/api'


def test_blockchain_config():
    """Test the blockchain config endpoint"""
    print("\n=== Testing /api/blockchain/config ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/blockchain/config")
        
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")
        
        data = response.json()
        print("Config data:", data)
        
        # Verify that the response contains the expected fields
        required_fields = [
            'dataPurchaseContractAddress',
            'fdcHubAddress',
            'fdcVerificationAddress',
            'rpcUrl',
            'daLayerApi'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print("Missing required fields:", missing_fields)
        else:
            print("✅ All required fields are present")
        
        return data
    except Exception as e:
        print(f"Error testing blockchain config: {str(e)}")
        return None


def test_blockchain_verify():
    """Test the blockchain verify endpoint"""
    print("\n=== Testing /api/blockchain/verify ===")
    
    try:
        # Generate a mock request ID using Web3's keccak function
        from web3 import Web3
        request_id = Web3.keccak(text=f"test-verify-{int(time.time())}").hex()
        
        response = requests.post(
            f"{API_BASE_URL}/blockchain/verify",
            headers={'Content-Type': 'application/json'},
            json={'requestId': request_id}
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")
        
        data = response.json()
        print("Verification result:", data)
        
        # Verify that the response contains the expected fields
        required_fields = [
            'verified',
            'status',
            'message',
            'attestationResponse',
            'proof'
        ]
        
        missing_fields = [field for field in required_fields if field not in data and data.get(field) is not False]
        
        if missing_fields:
            print("Missing required fields:", missing_fields)
        else:
            print("✅ All required fields are present")
        
        return data
    except Exception as e:
        print(f"Error testing blockchain verify: {str(e)}")
        return None


def test_blockchain_purchase():
    """Test the blockchain purchase endpoint"""
    print("\n=== Testing /api/blockchain/purchase ===")
    
    try:
        # Create mock purchase data
        purchase_data = {
            "dataType": "satellite.observation",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [12.5, 41.9],
                        [12.6, 41.9],
                        [12.6, 42.0],
                        [12.5, 42.0],
                        [12.5, 41.9]
                    ]
                ]
            },
            "startDate": "2023-04-01",
            "endDate": "2023-04-30",
            "price": 0.01
        }
        
        response = requests.post(
            f"{API_BASE_URL}/blockchain/purchase",
            headers={'Content-Type': 'application/json'},
            json=purchase_data
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP error! Status: {response.status_code}")
        
        data = response.json()
        print("Purchase result:", data)
        
        # Verify that the response contains the expected fields
        required_fields = [
            'success',
            'requestId',
            'transactionHash',
            'attestationTransactionHash',
            'message'
        ]
        
        missing_fields = [field for field in required_fields if field not in data and data.get(field) is not False]
        
        if missing_fields:
            print("Missing required fields:", missing_fields)
        else:
            print("✅ All required fields are present")
        
        return data
    except Exception as e:
        print(f"Error testing blockchain purchase: {str(e)}")
        return None


def run_tests():
    """Run all tests"""
    print("Starting blockchain API tests...")
    
    # Test blockchain config
    config_data = test_blockchain_config()
    
    # Test blockchain verify
    verify_data = test_blockchain_verify()
    
    # Test blockchain purchase
    purchase_data = test_blockchain_purchase()
    
    print("\n=== Test Summary ===")
    print(f"Config test: {'✅ Passed' if config_data else '❌ Failed'}")
    print(f"Verify test: {'✅ Passed' if verify_data else '❌ Failed'}")
    print(f"Purchase test: {'✅ Passed' if purchase_data else '❌ Failed'}")


if __name__ == "__main__":
    run_tests()
