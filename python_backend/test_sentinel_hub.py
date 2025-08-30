"""
Test script for Sentinel Hub API
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sentinel_hub_api():
    """Test the Sentinel Hub API directly"""
    print("Testing Sentinel Hub API...")
    
    # STEP 1: Get your access token using Sentinel Hub credentials
    # Use hardcoded credentials for testing
    CLIENT_ID = "sh-120b12f5-f881-4eb1-ae7a-62a6e6836df1"
    CLIENT_SECRET = "UjIyMiO3yOidtbr3Xlmw4T49sBk5bbaM"
    
    print(f"Using client ID: {CLIENT_ID}")
    
    token_response = requests.post(
        "https://services.sentinel-hub.com/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    
    print(f"Token response status: {token_response.status_code}")
    
    if token_response.status_code != 200:
        print(f"Failed to obtain access token. Response: {token_response.text}")
        return
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        print("Failed to obtain access token:", token_data)
        return
    
    print(f"Successfully obtained access token: {access_token[:20]}...")
    
    # STEP 2: Build and make the catalog search request
    SENTINEL_HUB_URL = 'https://services.sentinel-hub.com/api/v1/catalog/search'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        "datetime": "2024-01-01T00:00:00Z/2024-01-10T23:59:59Z",
        "collections": ["sentinel-2-l2a"],
        "bbox": [13.4, 50.4, 13.6, 50.6],
        "limit": 10
    }
    
    print(f"Making request to {SENTINEL_HUB_URL} with payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(SENTINEL_HUB_URL, headers=headers, json=payload)
    
    print(f"Search response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        features = data.get('features', [])
        print(f"Received {len(features)} features:")
        for feature in features:
            print(f"- ID: {feature['id']}, Date: {feature['properties']['datetime']}")
    else:
        print(f"Request failed with status {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_sentinel_hub_api()
