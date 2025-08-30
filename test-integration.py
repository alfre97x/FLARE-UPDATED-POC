#!/usr/bin/env python
"""
Integration test script for SpaceData Purchase Application
Tests both Copernicus API and Blockchain integration
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:5000"
TEST_COORDINATES = [[41.3, 2.1], [41.3, 2.3], [41.5, 2.3], [41.5, 2.1]]  # Barcelona area
TEST_START_DATE = "2023-04-15"
TEST_END_DATE = "2023-04-22"
TEST_DATA_TYPE = "S2MSI2A"

def print_header(message):
    """Print a header message"""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_success(message):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️ {message}")

def check_server_running():
    """Check if the server is running"""
    print_header("Checking if server is running")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print_success("Server is running")
            return True
        else:
            print_error(f"Server returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Make sure it's running on http://localhost:5000")
        return False

def test_copernicus_api():
    """Test the Copernicus API integration"""
    print_header("Testing Copernicus API Integration")
    
    # Test search endpoint
    print_info("Testing satellite data search...")
    search_payload = {
        "dataType": TEST_DATA_TYPE,
        "coordinates": TEST_COORDINATES,
        "startDate": TEST_START_DATE,
        "endDate": TEST_END_DATE
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/copernicus/search",
            json=search_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                print_success(f"Found {len(data['results'])} satellite data products")
                
                # Get the first product ID for further testing
                product_id = data["results"][0]["id"]
                print_info(f"Using product ID: {product_id}")
                
                # Test product data endpoint
                print_info("Testing product data retrieval...")
                product_response = requests.get(f"{API_BASE_URL}/api/copernicus/product/{product_id}")
                
                if product_response.status_code == 200:
                    product_data = product_response.json()
                    if "metadata" in product_data:
                        print_success("Successfully retrieved product metadata")
                    else:
                        print_error("Product metadata not found in response")
                    
                    if "preview" in product_data and product_data["preview"]["data"]:
                        print_success("Successfully retrieved product preview image")
                    else:
                        print_error("Product preview image not found in response")
                else:
                    print_error(f"Failed to retrieve product data: {product_response.status_code}")
            else:
                print_error("No satellite data products found")
        else:
            print_error(f"Search request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
    except Exception as e:
        print_error(f"Error testing Copernicus API: {str(e)}")

def test_blockchain_integration():
    """Test the blockchain integration"""
    print_header("Testing Blockchain Integration")
    
    # Check if blockchain configuration is available
    print_info("Checking blockchain configuration...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/blockchain/config")
        
        if response.status_code == 200:
            config = response.json()
            if "contract_addresses" in config and "datapurchase" in config["contract_addresses"]:
                print_success("Blockchain configuration is available")
                
                # Generate a request ID
                print_info("Generating request ID...")
                request_payload = {
                    "data_info": {
                        "dataType": TEST_DATA_TYPE,
                        "startDate": TEST_START_DATE,
                        "endDate": TEST_END_DATE,
                        "coordinates": json.dumps(TEST_COORDINATES),
                        "aiAnalysis": True
                    }
                }
                
                request_response = requests.post(
                    f"{API_BASE_URL}/api/blockchain/generate-request-id",
                    json=request_payload
                )
                
                if request_response.status_code == 200:
                    request_data = request_response.json()
                    if "request_id" in request_data:
                        print_success(f"Successfully generated request ID: {request_data['request_id']}")
                    else:
                        print_error("Request ID not found in response")
                else:
                    print_error(f"Failed to generate request ID: {request_response.status_code}")
            else:
                print_error("Contract addresses not found in configuration")
        else:
            print_error(f"Failed to get blockchain configuration: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing blockchain integration: {str(e)}")

def main():
    """Main function"""
    print_header("SpaceData Purchase Application Integration Test")
    
    # Check if server is running
    if not check_server_running():
        print_error("Server is not running. Please start the server and try again.")
        sys.exit(1)
    
    # Test Copernicus API
    test_copernicus_api()
    
    # Test blockchain integration
    test_blockchain_integration()
    
    print_header("Integration Test Complete")

if __name__ == "__main__":
    main()
