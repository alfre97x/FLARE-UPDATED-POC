import requests
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use credentials from .env file
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
token_data = token_res.json()

if "access_token" not in token_data:
    raise Exception("❌ No access token returned. Check your client ID/secret.")
    
access_token = token_data["access_token"]
print(f"✅ Successfully obtained access token")

# Step 2: Query Sentinel-2 products with specific filters
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

# Function to query Sentinel-2 data with specific filters
def query_sentinel2_data():
    # Create a filter query with a specific date range (July 1-15, 2023)
    filter_query = (
        "Collection/Name eq 'SENTINEL-2' and "
        "ContentDate/Start gt 2023-07-01T00:00:00.000Z and "
        "ContentDate/Start lt 2023-07-15T23:59:59.999Z and "
        "OData.CSC.Intersects(area=geography'SRID=4326;"
        "POLYGON((-10.0 35.0, -10.0 65.0, 30.0 65.0, 30.0 35.0, -10.0 35.0))')"
    )
    
    params = {
        "$filter": filter_query,
        "$top": 10,
        "$orderby": "ContentDate/Start desc"
    }
    
    print("\n📅 Querying for Sentinel-2 data (July 1-15, 2023, wider area)...")
    print(f"Filter: {filter_query}")
    
    response = requests.get(
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        headers=headers,
        params=params
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json().get("value", [])
        
        if not results:
            print("⚠️ No Sentinel-2 products found matching the criteria")
            return 0
        else:
            print(f"✅ Found {len(results)} Sentinel-2 products:")
            for r in results:
                print(f"- {r['Name']} | {r['ContentDate']['Start']}")
            
            # Print details of the first product
            if results:
                product = results[0]
                print("\nFirst product details:")
                print(f"ID: {product.get('Id')}")
                print(f"Name: {product.get('Name')}")
                print(f"Date: {product.get('ContentDate', {}).get('Start')}")
                
                # Print attributes if available
                if 'Attributes' in product:
                    print("\nAttributes:")
                    for attr_type in product['Attributes']:
                        if isinstance(product['Attributes'][attr_type], list):
                            for attr in product['Attributes'][attr_type]:
                                if 'Name' in attr and 'Value' in attr:
                                    print(f"- {attr['Name']}: {attr['Value']}")
            
            return len(results)
    else:
        print(f"❌ API request failed: {response.text}")
        return 0

# Execute the query
print("\n=== Starting query for Sentinel-2 data with specific filters ===")
products_found = query_sentinel2_data()
print(f"\n🔍 Total Sentinel-2 products found: {products_found}")

# Try with different product type if no results
if products_found == 0:
    print("\n=== Trying with minimal filters and no spatial filter ===")
    # Create a very simple filter query with the specific date range but no spatial filter
    filter_query = (
        "Collection/Name eq 'SENTINEL-2' and "
        "ContentDate/Start gt 2023-07-01T00:00:00.000Z and "
        "ContentDate/Start lt 2023-07-15T23:59:59.999Z"
    )
    
    params = {
        "$filter": filter_query,
        "$top": 10,
        "$orderby": "ContentDate/Start desc"
    }
    
    print("\n📅 Querying for Sentinel-2 data (July 1-15, 2023, no spatial filter)...")
    print(f"Filter: {filter_query}")
    
    response = requests.get(
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        headers=headers,
        params=params
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json().get("value", [])
        
        if not results:
            print("⚠️ No Sentinel-2 products found matching the criteria")
        else:
            print(f"✅ Found {len(results)} Sentinel-2 products:")
            for r in results:
                print(f"- {r['Name']} | {r['ContentDate']['Start']}")
            
            # Print details of the first product
            if results:
                product = results[0]
                print("\nFirst product details:")
                print(f"ID: {product.get('Id')}")
                print(f"Name: {product.get('Name')}")
                print(f"Date: {product.get('ContentDate', {}).get('Start')}")
                
                # Print attributes if available
                if 'Attributes' in product:
                    print("\nAttributes:")
                    for attr_type in product['Attributes']:
                        if isinstance(product['Attributes'][attr_type], list):
                            for attr in product['Attributes'][attr_type]:
                                if 'Name' in attr and 'Value' in attr:
                                    print(f"- {attr['Name']}: {attr['Value']}")
            
            products_found += len(results)
    else:
        print(f"❌ API request failed: {response.text}")

print(f"\n🔍 Grand total of Sentinel-2 products found: {products_found}")
