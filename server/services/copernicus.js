/**
 * Copernicus Data Space Ecosystem (CDSE) service
 * Handles API calls to the Copernicus Data Space Ecosystem
 * Updated to use STAC API for better compatibility
 */

const axios = require('axios');
const config = require('../config');

// Token management
let accessToken = null;
let tokenExpiry = 0;

/**
 * Get access token for Copernicus API
 * @returns {Promise<string|null>} Access token or null if authentication is skipped
 */
const getAccessToken = async () => {
  const now = Date.now();
  
  // Return cached token if still valid
  if (accessToken && now < tokenExpiry - 60000) { // 1 minute buffer
    return accessToken;
  }
  
  // Check if credentials are provided
  if (!config.cdse.clientId || !config.cdse.clientSecret) {
    console.log('No CDSE credentials provided. Skipping authentication.');
    return null;
  }
  
  try {
    console.log('Getting new CDSE access token...');
    
    // Request new token
    const response = await axios.post(
      config.cdse.tokenUrl,
      new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: config.cdse.clientId,
        client_secret: config.cdse.clientSecret
      }),
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      }
    );
    
    // Store token and expiry
    accessToken = response.data.access_token;
    tokenExpiry = now + (response.data.expires_in * 1000);
    
    console.log('Successfully obtained CDSE access token');
    return accessToken;
  } catch (error) {
    console.error('Error getting CDSE access token:', error.message);
    console.log('Proceeding without authentication (some features may be limited)');
    return null;
  }
};

/**
 * Convert coordinates array to WKT POLYGON format
 * @param {Array} coords Array of [lat, lng] coordinates
 * @returns {string} WKT POLYGON string
 */
const coordinatesToWkt = (coords) => {
  if (!coords || !coords.length) {
    // Default to a small area around Barcelona for demo
    return 'POLYGON((2.1 41.3, 2.3 41.3, 2.3 41.5, 2.1 41.5, 2.1 41.3))';
  }
  
  // Format coordinates as "lng lat" pairs (note the order: longitude first, then latitude)
  const formattedCoords = coords.map(point => `${point[1]} ${point[0]}`);
  
  // Close the polygon by repeating the first point
  if (formattedCoords.length > 0 && formattedCoords[0] !== formattedCoords[formattedCoords.length - 1]) {
    formattedCoords.push(formattedCoords[0]);
  }
  
  // Create WKT POLYGON string
  return `POLYGON((${formattedCoords.join(', ')}))`;
};

/**
 * Convert coordinates array to bounding box format for STAC API
 * @param {Array} coords Array of [lat, lng] coordinates
 * @returns {Array} Bounding box [west, south, east, north]
 */
const coordinatesToBbox = (coords) => {
  if (!coords || !coords.length) {
    // Default to a bounding box around Barcelona for demo
    return [2.1, 41.3, 2.3, 41.5]; // [west, south, east, north]
  }
  
  // Extract lat/lng values
  const lats = coords.map(point => point[0]);
  const lngs = coords.map(point => point[1]);
  
  // Calculate bounding box
  const west = Math.min(...lngs);
  const south = Math.min(...lats);
  const east = Math.max(...lngs);
  const north = Math.max(...lats);
  
  return [west, south, east, north];
};

/**
 * Search for satellite data based on criteria using STAC API
 * @param {Object} params Search parameters
 * @param {string} params.dataType Data type ID
 * @param {Array} params.coordinates Array of [lat, lng] coordinates
 * @param {string} params.startDate Start date (YYYY-MM-DD)
 * @param {string} params.endDate End date (YYYY-MM-DD)
 * @returns {Promise<Array>} Array of search results
 */
const searchSatelliteData = async (params) => {
  try {
    // Get access token
    const token = await getAccessToken();
    
    // Extract parameters
    const { dataType, coordinates, startDate, endDate } = params;
    
    // Convert coordinates to bounding box for STAC API
    const bbox = coordinatesToBbox(coordinates);
    
    // Format dates for STAC API
    const formattedStartDate = startDate + 'T00:00:00Z';
    const formattedEndDate = endDate + 'T23:59:59Z';
    const dateRange = `${formattedStartDate}/${formattedEndDate}`;
    
    console.log('Searching for satellite data with params:', {
      dataType,
      bbox,
      dateRange
    });
    
    // Map OData data types to STAC collections
    const collectionMap = {
      'S2MSI2A': 'sentinel-2-l2a',
      'S1GRD': 'sentinel-1-grd',
      'S3OLCI': 'sentinel-3-olci',
      // Add more mappings as needed
    };
    
    // Get the STAC collection name
    const collection = collectionMap[dataType] || 'sentinel-2-l2a';
    
    // Build STAC API search payload
    const searchPayload = {
      collections: [collection],
      bbox: bbox,
      datetime: dateRange,
      filter: {
        op: "and",
        args: [
          {
            op: "<=",
            args: [
              { property: "eo:cloud_cover" },
              100 // Default to 100% cloud cover, can be adjusted
            ]
          }
        ]
      },
      limit: 10
    };
    
    // Build URL for STAC API search
    const url = `${config.cdse.stacUrl}/search`;
    
    console.log('STAC API URL:', url);
    console.log('STAC API payload:', JSON.stringify(searchPayload, null, 2));
    
    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    // Add authorization header if token is available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Make the API request
    const response = await axios.post(url, searchPayload, { headers });
    
    // Extract features from STAC response
    const features = response.data.features || [];
    
    console.log(`Found ${features.length} results`);
    
    // Convert STAC features to OData-like format for compatibility
    const results = features.map(feature => {
      return {
        Id: feature.id,
        Name: feature.id,
        ContentType: dataType,
        ContentDate: {
          Start: feature.properties.datetime,
          End: feature.properties.datetime
        },
        CloudCoverPercentage: feature.properties['eo:cloud_cover'] || 0,
        Footprint: feature.geometry ? JSON.stringify(feature.geometry) : null,
        // Add STAC-specific properties
        stac_version: feature.stac_version,
        stac_extensions: feature.stac_extensions,
        geometry: feature.geometry,
        bbox: feature.bbox,
        properties: feature.properties,
        assets: feature.assets,
        links: feature.links
      };
    });
    
    return results;
  } catch (error) {
    console.error('Error searching for satellite data:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw new Error('Failed to search for satellite data');
  }
};

/**
 * Get preview image for a product using STAC API
 * @param {string} productId Product ID
 * @returns {Promise<Object>} Preview image data
 */
const getProductPreview = async (productId) => {
  try {
    // Get access token
    const token = await getAccessToken();
    
    console.log('Getting preview image for product:', productId);
    
    // First, get the product metadata to find the thumbnail URL
    const metadata = await getProductMetadata(productId);
    
    // Check if we have assets with thumbnails
    if (metadata.assets) {
      // Try to get thumbnail or preview image
      const thumbnailAsset = metadata.assets.thumbnail || 
                            metadata.assets.preview || 
                            metadata.assets.overview ||
                            metadata.assets.browse;
      
      if (thumbnailAsset && thumbnailAsset.href) {
        console.log('Found thumbnail URL:', thumbnailAsset.href);
        
        // Prepare headers
        const headers = {
          'Accept': 'image/*',
          'Accept-Encoding': 'gzip, deflate'
        };
        
        // Add authorization header if token is available
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Get the thumbnail
        const response = await axios.get(thumbnailAsset.href, {
          headers,
          responseType: 'arraybuffer'
        });
        
        return {
          data: response.data,
          contentType: thumbnailAsset.type || 'image/jpeg',
          source: 'stac_thumbnail'
        };
      }
    }
    
    // Fallback to OData API for thumbnails if STAC doesn't provide them
    try {
      const previewUrl = `${config.cdse.apiUrl}('${productId}')/Products('Quicklook')/$value`;
      console.log('Falling back to OData quicklook URL:', previewUrl);
      
      // Prepare headers
      const headers = {
        'Accept': 'image/*',
        'Accept-Encoding': 'gzip, deflate'
      };
      
      // Add authorization header if token is available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await axios.get(previewUrl, {
        headers,
        responseType: 'arraybuffer'
      });
      
      return {
        data: response.data,
        contentType: response.headers['content-type'] || 'image/jpeg',
        source: 'odata_quicklook'
      };
    } catch (previewError) {
      console.warn('OData quicklook not available, trying thumbnail...');
      
      // If quicklook fails, try thumbnail
      const thumbnailUrl = `${config.cdse.apiUrl}('${productId}')/Products('Thumbnail')/$value`;
      console.log('Trying OData thumbnail URL:', thumbnailUrl);
      
      // Prepare headers
      const headers = {
        'Accept': 'image/*',
        'Accept-Encoding': 'gzip, deflate'
      };
      
      // Add authorization header if token is available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await axios.get(thumbnailUrl, {
        headers,
        responseType: 'arraybuffer'
      });
      
      return {
        data: response.data,
        contentType: response.headers['content-type'] || 'image/jpeg',
        source: 'odata_thumbnail'
      };
    }
  } catch (error) {
    console.error('Error getting product preview:', error.message);
    throw new Error('Failed to get product preview');
  }
};

/**
 * Get product metadata using STAC API
 * @param {string} productId Product ID
 * @returns {Promise<Object>} Product metadata
 */
const getProductMetadata = async (productId) => {
  try {
    // Get access token
    const token = await getAccessToken();
    
    console.log('Getting metadata for product:', productId);
    
    // Build URL for STAC API item
    // Note: This assumes the productId is a valid STAC item ID
    // In a real implementation, you might need to search for the item first
    
    // First try to get the item directly
    try {
      // We don't know which collection the item belongs to, so we need to search for it
      const searchPayload = {
        ids: [productId],
        limit: 1
      };
      
      const searchUrl = `${config.cdse.stacUrl}/search`;
      console.log('Searching for item by ID:', searchUrl);
      
      // Prepare headers
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
      
      // Add authorization header if token is available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const searchResponse = await axios.post(searchUrl, searchPayload, { headers });
      
      const features = searchResponse.data.features || [];
      
      if (features.length > 0) {
        console.log('Found item in STAC API');
        return features[0];
      } else {
        throw new Error('Item not found in STAC API');
      }
    } catch (stacError) {
      console.warn('Error getting item from STAC API:', stacError.message);
      console.warn('Falling back to OData API for metadata');
      
      // Fallback to OData API
      const url = `${config.cdse.apiUrl}('${productId}')`;
      // Prepare headers
      const headers = {
        'Accept': 'application/json'
      };
      
      // Add authorization header if token is available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await axios.get(url, { headers });
      
      return response.data;
    }
  } catch (error) {
    console.error('Error getting product metadata:', error.message);
    throw new Error('Failed to get product metadata');
  }
};

module.exports = {
  getAccessToken,
  searchSatelliteData,
  getProductPreview,
  getProductMetadata,
  coordinatesToWkt,
  coordinatesToBbox
};
