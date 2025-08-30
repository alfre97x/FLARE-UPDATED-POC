import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use credentials from .env file if available
client_id = os.getenv('CDSE_CLIENT_ID')
client_secret = os.getenv('CDSE_CLIENT_SECRET')

# Check if we need to authenticate
need_auth = client_id and client_secret

# Function to get access token if credentials are available
def get_access_token():
    if not need_auth:
        print("No credentials found in .env file. Proceeding without authentication.")
        return None
    
    print("Requesting CDSE token...")
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    token_res = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
    )
    token_data = token_res.json()

    if "access_token" not in token_data:
        raise Exception("❌ No access token returned. Check your client ID/secret.")
        
    print(f"✅ Successfully obtained access token")
    return token_data["access_token"]

# Get access token if needed
access_token = get_access_token() if need_auth else None

# Set up headers
headers = {
    "Content-Type": "application/json"
}

# Add authorization header if we have a token
if access_token:
    headers["Authorization"] = f"Bearer {access_token}"

# Function to search for Sentinel-2 data using STAC API
def search_sentinel2_data(date_start, date_end, bbox, cloud_cover_max=100, limit=10):
    # Format the datetime range
    datetime_range = f"{date_start}/{date_end}"
    
    # Define the search parameters
    search_payload = {
        "collections": ["sentinel-2-l2a"],  # Using Level-2A products
        "bbox": bbox,  # Bounding box coordinates [west, south, east, north]
        "datetime": datetime_range,
        "filter": {
            "op": "and",
            "args": [
                {
                    "op": "<=",
                    "args": [
                        {"property": "eo:cloud_cover"},
                        cloud_cover_max
                    ]
                }
            ]
        },
        "limit": limit
    }
    
    print(f"\n📅 Searching for Sentinel-2 L2A data ({date_start} to {date_end})...")
    print(f"Area: {bbox}")
    print(f"Cloud cover: <= {cloud_cover_max}%")
    
    # Send the POST request
    response = requests.post(
        "https://stac.dataspace.copernicus.eu/v1/search",
        headers=headers,
        data=json.dumps(search_payload)
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        features = results.get("features", [])
        
        if not features:
            print("⚠️ No Sentinel-2 products found matching the criteria")
            return 0
        else:
            print(f"✅ Found {len(features)} Sentinel-2 products:")
            for item in features:
                print(f"- ID: {item['id']}")
                print(f"  Date: {item['properties'].get('datetime')}")
                print(f"  Cloud Cover: {item['properties'].get('eo:cloud_cover', 'N/A')}%")
                if 'assets' in item and 'data' in item['assets']:
                    print(f"  Download Link: {item['assets']['data']['href']}")
                print()
            
            # Print more details of the first product
            if features:
                item = features[0]
                print("\nFirst product details:")
                print(f"ID: {item['id']}")
                print(f"Date: {item['properties'].get('datetime')}")
                print(f"Cloud Cover: {item['properties'].get('eo:cloud_cover', 'N/A')}%")
                
                # Print all available assets
                if 'assets' in item:
                    print("\nAvailable assets:")
                    for asset_name, asset_info in item['assets'].items():
                        print(f"- {asset_name}: {asset_info.get('title', 'No title')}")
                        if 'href' in asset_info:
                            print(f"  URL: {asset_info['href']}")
                
                # Print all properties
                print("\nProperties:")
                for prop_name, prop_value in item['properties'].items():
                    print(f"- {prop_name}: {prop_value}")
            
            return len(features)
    else:
        print(f"❌ API request failed: {response.text}")
        return 0

# Execute searches with different parameters

print("\n=== Testing STAC API for Sentinel-2 data ===")

# Search 1: Western Europe, July 1-15, 2023, low cloud cover
products_found = search_sentinel2_data(
    date_start="2023-07-01T00:00:00Z",
    date_end="2023-07-15T23:59:59Z",
    bbox=[-10.0, 35.0, 30.0, 65.0],  # Western Europe
    cloud_cover_max=10
)
print(f"\n🔍 Total Sentinel-2 products found (July 2023, low cloud cover): {products_found}")

# If no results, try with higher cloud cover
if products_found == 0:
    print("\n=== Trying with higher cloud cover limit ===")
    products_found = search_sentinel2_data(
        date_start="2023-07-01T00:00:00Z",
        date_end="2023-07-15T23:59:59Z",
        bbox=[-10.0, 35.0, 30.0, 65.0],  # Western Europe
        cloud_cover_max=50
    )
    print(f"\n🔍 Total Sentinel-2 products found (July 2023, medium cloud cover): {products_found}")

# Try with September 2023 as suggested in the example
if products_found == 0:
    print("\n=== Trying with September 2023 ===")
    products_found = search_sentinel2_data(
        date_start="2023-09-01T00:00:00Z",
        date_end="2023-09-30T23:59:59Z",
        bbox=[-10.0, 35.0, 30.0, 65.0],  # Western Europe
        cloud_cover_max=10
    )
    print(f"\n🔍 Total Sentinel-2 products found (September 2023, low cloud cover): {products_found}")

print(f"\n🔍 Grand total of Sentinel-2 products found: {products_found}")
