"""
Copernicus Data Space Ecosystem (CDSE) API client
Handles API calls to the Copernicus Data Space Ecosystem using STAC API
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_URL = "https://stac.dataspace.copernicus.eu/v1"
ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# Token management
access_token = None
token_expiry = 0

def get_access_token():
    """
    Get access token for Copernicus API
    Returns:
        str|None: Access token or None if authentication is skipped
    """
    global access_token, token_expiry
    
    import time
    now = int(time.time() * 1000)
    
    # Return cached token if still valid
    if access_token and now < token_expiry - 60000:  # 1 minute buffer
        return access_token
    
    # Get credentials from environment variables
    client_id = os.getenv('CDSE_CLIENT_ID')
    client_secret = os.getenv('CDSE_CLIENT_SECRET')
    
    # Check if credentials are provided
    if not client_id or not client_secret:
        logger.info('No CDSE credentials provided. Skipping authentication.')
        return None
    
    try:
        logger.info('Getting new CDSE access token...')
        
        # Request new token
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get access token: {response.text}")
            return None
        
        token_data = response.json()
        
        # Store token and expiry
        access_token = token_data["access_token"]
        token_expiry = now + (token_data["expires_in"] * 1000)
        
        logger.info('Successfully obtained CDSE access token')
        return access_token
    except Exception as e:
        logger.error(f'Error getting CDSE access token: {str(e)}')
        logger.info('Proceeding without authentication (some features may be limited)')
        return None

def coordinates_to_bbox(coords):
    """
    Convert coordinates array to bounding box format for STAC API
    Args:
        coords (list): Array of [lat, lng] coordinates or string representation
    Returns:
        list: Bounding box [west, south, east, north]
    """
    # Handle string representation of coordinates
    if isinstance(coords, str):
        try:
            # Try to parse as JSON
            coords = json.loads(coords)
        except json.JSONDecodeError:
            # If not valid JSON, return default bbox
            logger.warning(f"Invalid coordinates format: {coords}")
            return [2.1, 41.3, 2.3, 41.5]  # Default to Barcelona area
    
    if not coords or not isinstance(coords, list) or len(coords) < 3:
        # Default to a bounding box around Barcelona for demo
        return [2.1, 41.3, 2.3, 41.5]  # [west, south, east, north]
    
    # Extract lat/lng values
    lats = [point[0] for point in coords]
    lngs = [point[1] for point in coords]
    
    # Calculate bounding box
    west = min(lngs)
    south = min(lats)
    east = max(lngs)
    north = max(lats)
    
    return [west, south, east, north]

def expand_date_range(start_date_str, end_date_str, days_before, days_after):
    """
    Expand date range by specified number of days
    Args:
        start_date_str (str): Start date string (YYYY-MM-DD)
        end_date_str (str): End date string (YYYY-MM-DD)
        days_before (int): Number of days to subtract from start date
        days_after (int): Number of days to add to end date
    Returns:
        tuple: (new_start_date_str, new_end_date_str)
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        new_start = start_date - timedelta(days=days_before)
        new_end = end_date + timedelta(days=days_after)
        
        return new_start.strftime('%Y-%m-%d'), new_end.strftime('%Y-%m-%d')
    except Exception as e:
        logger.warning(f"Error expanding date range: {str(e)}")
        return start_date_str, end_date_str

def perform_stac_search(token, collection, bbox, date_range, cloud_cover_max, limit):
    """
    Perform a single STAC API search with given parameters
    Args:
        token (str): Access token
        collection (str): STAC collection name
        bbox (list): Bounding box coordinates
        date_range (str): Date range string
        cloud_cover_max (int): Maximum cloud coverage percentage
        limit (int): Maximum results to return
    Returns:
        list: List of features found, or empty list if error
    """
    try:
        # Build STAC API search payload with cloud coverage filter
        search_payload = {
            "collections": [collection],
            "bbox": bbox,
            "datetime": date_range,
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
            "limit": limit,
            "sortby": [
                {
                    "field": "eo:cloud_cover",
                    "direction": "asc"  # Sort by lowest cloud coverage first
                }
            ]
        }
        
        # Build URL for STAC API search
        url = f"{STAC_URL}/search"
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authorization header if token is available
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        # Make the API request
        response = requests.post(url, headers=headers, json=search_payload)
        
        if response.status_code != 200:
            logger.error(f"STAC API request failed: {response.text}")
            return []
        
        # Extract features from STAC response
        features = response.json().get('features', [])
        return features
        
    except Exception as e:
        logger.error(f'Error in STAC search: {str(e)}')
        return []

def search_satellite_data(data_type, coordinates, start_date, end_date, cloud_cover_max=10, limit=10):
    """
    Search for satellite data based on criteria using STAC API with progressive fallback
    Args:
        data_type (str): Data type ID (e.g., 'S2MSI2A')
        coordinates (list): Array of [lat, lng] coordinates
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        cloud_cover_max (int): Maximum cloud cover percentage (default: 10 for very clear images)
        limit (int): Maximum number of results to return
    Returns:
        list: Array of search results with low cloud coverage and search metadata
    """
    try:
        # Get access token
        token = get_access_token()
        
        # Convert coordinates to bounding box for STAC API
        bbox = coordinates_to_bbox(coordinates)
        
        # Map OData data types to STAC collections
        collection_map = {
            'S2MSI2A': 'sentinel-2-l2a',
            'S1GRD': 'sentinel-1-grd',
            'S3OLCI': 'sentinel-3-olci',
            # Add more mappings as needed
        }
        
        # Get the STAC collection name
        collection = collection_map.get(data_type, 'sentinel-2-l2a')
        
        logger.info(f'Starting progressive search for {data_type} with ≤{cloud_cover_max}% cloud coverage')
        
        # Define search strategies with progressive fallback
        search_strategies = [
            # Phase 1: Try original date range with low cloud coverage
            {'days_before': 0, 'days_after': 0, 'cloud_max': cloud_cover_max, 'description': 'original date range'},
            
            # Phase 2: Expand date range while keeping low cloud coverage
            {'days_before': 7, 'days_after': 7, 'cloud_max': cloud_cover_max, 'description': '±1 week expanded'},
            {'days_before': 14, 'days_after': 14, 'cloud_max': cloud_cover_max, 'description': '±2 weeks expanded'},
            {'days_before': 30, 'days_after': 30, 'cloud_max': cloud_cover_max, 'description': '±1 month expanded'},
            
            # Phase 3: If still no results, try higher cloud coverage with expanded dates
            {'days_before': 7, 'days_after': 7, 'cloud_max': 15, 'description': '±1 week, 15% clouds'},
            {'days_before': 14, 'days_after': 14, 'cloud_max': 15, 'description': '±2 weeks, 15% clouds'},
            {'days_before': 30, 'days_after': 30, 'cloud_max': 20, 'description': '±1 month, 20% clouds'}
        ]
        
        # Track search results
        final_results = []
        search_info = {
            'strategy_used': None,
            'actual_date_range': None,
            'cloud_coverage_used': cloud_cover_max,
            'total_attempts': 0
        }
        
        # Try each search strategy progressively
        for strategy in search_strategies:
            search_info['total_attempts'] += 1
            
            # Expand date range
            expanded_start, expanded_end = expand_date_range(
                start_date, end_date, 
                strategy['days_before'], strategy['days_after']
            )
            
            # Format dates for STAC API
            formatted_start = f"{expanded_start}T00:00:00Z"
            formatted_end = f"{expanded_end}T23:59:59Z"
            date_range = f"{formatted_start}/{formatted_end}"
            
            logger.info(f'Attempt {search_info["total_attempts"]}: Searching with {strategy["description"]} (≤{strategy["cloud_max"]}% clouds)')
            logger.info(f'  Date range: {expanded_start} to {expanded_end}')
            
            # Perform the search
            features = perform_stac_search(
                token, collection, bbox, date_range, 
                strategy['cloud_max'], limit
            )
            
            if features:
                logger.info(f'SUCCESS: Found {len(features)} images using {strategy["description"]}')
                
                # Update search info
                search_info['strategy_used'] = strategy['description']
                search_info['actual_date_range'] = f"{expanded_start} to {expanded_end}"
                search_info['cloud_coverage_used'] = strategy['cloud_max']
                
                # Log cloud coverage for each result
                for feature in features[:3]:  # Log first 3 results
                    cloud_cover = feature['properties'].get('eo:cloud_cover', 'N/A')
                    logger.info(f'  - {feature["id"]}: {cloud_cover}% cloud coverage')
                
                # Convert STAC features to simplified format
                for feature in features:
                    # Find thumbnail or preview image
                    thumbnail_url = None
                    if 'assets' in feature:
                        for asset_type in ['thumbnail', 'preview', 'overview', 'browse']:
                            if asset_type in feature['assets'] and 'href' in feature['assets'][asset_type]:
                                thumbnail_url = feature['assets'][asset_type]['href']
                                break
                    
                    # Create result object
                    result = {
                        'id': feature['id'],
                        'name': feature['id'],
                        'datetime': feature['properties'].get('datetime'),
                        'cloud_cover': feature['properties'].get('eo:cloud_cover', 0),
                        'thumbnail_url': thumbnail_url,
                        'assets': feature.get('assets', {}),
                        'properties': feature.get('properties', {}),
                        'bbox': feature.get('bbox'),
                        'geometry': feature.get('geometry'),
                        # Add search metadata
                        'search_strategy': strategy['description'],
                        'search_date_range': f"{expanded_start} to {expanded_end}"
                    }
                    
                    final_results.append(result)
                
                # Success - return results
                break
            else:
                logger.info(f'  No results found with {strategy["description"]}')
        
        # Log final results
        if final_results:
            logger.info(f'FINAL RESULT: Found {len(final_results)} images after {search_info["total_attempts"]} attempts')
            logger.info(f'  Strategy: {search_info["strategy_used"]}')
            logger.info(f'  Date range: {search_info["actual_date_range"]}')
            logger.info(f'  Max cloud coverage: {search_info["cloud_coverage_used"]}%')
        else:
            logger.warning(f'NO RESULTS: No suitable images found after {search_info["total_attempts"]} attempts')
            logger.info('  Try expanding the search area or using a different time period')
        
        return final_results
        
    except Exception as e:
        logger.error(f'Error in progressive satellite data search: {str(e)}')
        return []

def get_product_preview(product_id):
    """
    Get preview image for a product
    Args:
        product_id (str): Product ID
    Returns:
        dict: Preview image data with content type
    """
    try:
        # Get access token
        token = get_access_token()
        
        logger.info(f'Getting preview image for product: {product_id}')
        
        # Prepare headers
        headers = {
            'Accept': 'image/*',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        # Add authorization header if token is available
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        # Try to get the product metadata to find the thumbnail URL
        try:
            # Search for the product by ID
            search_payload = {
                "ids": [product_id],
                "limit": 1
            }
            
            search_url = f"{STAC_URL}/search"
            search_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            if token:
                search_headers['Authorization'] = f"Bearer {token}"
            
            search_response = requests.post(search_url, headers=search_headers, json=search_payload)
            
            if search_response.status_code == 200:
                features = search_response.json().get('features', [])
                
                if features:
                    feature = features[0]
                    
                    # Check if we have assets with thumbnails
                    if 'assets' in feature:
                        # Try to get thumbnail or preview image
                        for asset_type in ['thumbnail', 'preview', 'overview', 'browse']:
                            if asset_type in feature['assets'] and 'href' in feature['assets'][asset_type]:
                                thumbnail_url = feature['assets'][asset_type]['href']
                                logger.info(f'Found thumbnail URL: {thumbnail_url}')
                                
                                # Get the thumbnail
                                response = requests.get(thumbnail_url, headers=headers)
                                
                                if response.status_code == 200:
                                    return {
                                        'data': response.content,
                                        'content_type': response.headers.get('content-type', 'image/jpeg'),
                                        'source': f'stac_{asset_type}'
                                    }
        except Exception as e:
            logger.warning(f'Error getting product metadata from STAC API: {str(e)}')
        
        # Fallback to OData API for thumbnails if STAC doesn't provide them
        try:
            preview_url = f"{ODATA_URL}('{product_id}')/Products('Quicklook')/$value"
            logger.info(f'Falling back to OData quicklook URL: {preview_url}')
            
            response = requests.get(preview_url, headers=headers)
            
            if response.status_code == 200:
                return {
                    'data': response.content,
                    'content_type': response.headers.get('content-type', 'image/jpeg'),
                    'source': 'odata_quicklook'
                }
        except Exception as e:
            logger.warning(f'Error getting quicklook from OData API: {str(e)}')
            
            # If quicklook fails, try thumbnail
            try:
                thumbnail_url = f"{ODATA_URL}('{product_id}')/Products('Thumbnail')/$value"
                logger.info(f'Trying OData thumbnail URL: {thumbnail_url}')
                
                response = requests.get(thumbnail_url, headers=headers)
                
                if response.status_code == 200:
                    return {
                        'data': response.content,
                        'content_type': response.headers.get('content-type', 'image/jpeg'),
                        'source': 'odata_thumbnail'
                    }
            except Exception as e:
                logger.warning(f'Error getting thumbnail from OData API: {str(e)}')
        
        # If all attempts fail, return None
        logger.error('Failed to get product preview')
        return None
    except Exception as e:
        logger.error(f'Error getting product preview: {str(e)}')
        return None

def get_product_metadata(product_id):
    """
    Get product metadata
    Args:
        product_id (str): Product ID
    Returns:
        dict: Product metadata
    """
    try:
        # Get access token
        token = get_access_token()
        
        logger.info(f'Getting metadata for product: {product_id}')
        
        # Try to get the item from STAC API
        try:
            # Search for the product by ID
            search_payload = {
                "ids": [product_id],
                "limit": 1
            }
            
            search_url = f"{STAC_URL}/search"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Add authorization header if token is available
            if token:
                headers['Authorization'] = f"Bearer {token}"
            
            search_response = requests.post(search_url, headers=headers, json=search_payload)
            
            if search_response.status_code == 200:
                features = search_response.json().get('features', [])
                
                if features:
                    logger.info('Found item in STAC API')
                    return features[0]
        except Exception as e:
            logger.warning(f'Error getting item from STAC API: {str(e)}')
        
        # Fallback to OData API
        try:
            url = f"{ODATA_URL}('{product_id}')"
            
            # Prepare headers
            headers = {
                'Accept': 'application/json'
            }
            
            # Add authorization header if token is available
            if token:
                headers['Authorization'] = f"Bearer {token}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info('Found item in OData API')
                return response.json()
        except Exception as e:
            logger.warning(f'Error getting item from OData API: {str(e)}')
        
        # If all attempts fail, return None
        logger.error('Failed to get product metadata')
        return None
    except Exception as e:
        logger.error(f'Error getting product metadata: {str(e)}')
        return None
