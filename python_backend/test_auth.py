import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Copernicus Data Space Ecosystem (CDSE) credentials
client_id = os.getenv('CDSE_CLIENT_ID')
client_secret = os.getenv('CDSE_CLIENT_SECRET')

# Step 1: Get access token
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

print(f"Status code: {token_res.status_code}")
print(f"Response: {token_res.text}")

if token_res.status_code == 200:
    access_token = token_res.json()["access_token"]
    print(f"Access token: {access_token[:20]}...")
    
    # Step 2: Query Sentinel-1 products over Rome
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    # Try with a wider date range and a different area (Paris)
    filter_query = (
        "contains(Name,'S1') and "
        "ContentDate/Start gt 2022-01-01T00:00:00.000Z and "
        "ContentDate/Start lt 2023-12-31T23:59:59.999Z and "
        "OData.CSC.Intersects(area=geography'SRID=4326;"
        "POLYGON((2.0 48.6, 2.0 49.0, 2.6 49.0, 2.6 48.6, 2.0 48.6))')"
    )
    
    params = {
        "$filter": filter_query,
        "$top": 5,
        "$orderby": "ContentDate/Start desc"
    }
    
    print("\nTesting CDSE API with Sentinel-1 query over Rome...")
    print(f"Filter: {filter_query}")
    
    response = requests.get(
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        headers=headers,
        params=params
    )
    
    print(f"API response status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json().get("value", [])
        
        if not results:
            print("⚠️ No Sentinel-1 products found.")
        else:
            print(f"✅ Found {len(results)} products:")
            for r in results:
                print(f"- {r['Name']} | {r['ContentDate']['Start']}")
                
            # Print details of the first product
            if results:
                product = results[0]
                print("\nFirst product details:")
                print(f"ID: {product.get('Id')}")
                print(f"Name: {product.get('Name')}")
                print(f"Date: {product.get('ContentDate', {}).get('Start')}")
                print(f"Platform: {product.get('Attributes', {}).get('Platform', 'N/A')}")
                
                # Try to get the thumbnail URL
                thumbnail_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product.get('Id')})/Products('Thumbnail')/$value"
                print(f"Thumbnail URL: {thumbnail_url}")
    else:
        print(f"API request failed: {response.text}")
else:
    print("Failed to get token")
