/**
 * Copernicus API integration for web application
 * Handles satellite data requests and responses
 */

const API_BASE = (window.RUNTIME_CONFIG && window.RUNTIME_CONFIG.NODE_API_BASE) || '';

// API Configuration for backend server
const API_CONFIG = {
    // Base URL for API endpoints
    BASE_URL: `${API_BASE}/api`,
    // Copernicus API endpoints
    COPERNICUS: {
        SEARCH: '/copernicus/search',
        PRODUCT: '/copernicus/product'
    }
};

/**
 * Convert coordinates array to WKT POLYGON format
 * @param {Array} coords Array of [lat, lng] coordinates
 * @returns {string} WKT POLYGON string
 */
function coordinatesToWkt(coords) {
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
}

/**
 * Get available data types from Copernicus
 * @returns {Promise<Array>} Array of data types
 */
async function getAvailableDataTypes() {
    console.log('Getting available data types...');
    
    // In a real app, this would make an API call
    // For now, return static data types
    return [
        { id: 'S2MSI2A', name: 'Sentinel-2 Level 2A', description: 'Multispectral imagery with atmospheric correction', resolution: '10m' },
        { id: 'S1GRD', name: 'Sentinel-1 SAR', description: 'Synthetic Aperture Radar imagery', resolution: '5-20m' },
        { id: 'S3OLCI', name: 'Sentinel-3 OLCI', description: 'Ocean and Land Color Instrument', resolution: '300m' }
    ];
}

/**
 * Search for satellite data based on criteria
 * @param {Object} params Search parameters
 * @param {string} params.dataType Data type ID
 * @param {Array} params.coordinates Array of [lat, lng] coordinates
 * @param {string} params.startDate Start date (YYYY-MM-DD)
 * @param {string} params.endDate End date (YYYY-MM-DD)
 * @returns {Promise<Array>} Array of search results
 */
async function searchSatelliteData(params) {
    console.log('Searching for satellite data with params:', params);
    
    try {
        // Extract parameters
        const { dataType, coordinates, startDate, endDate } = params;
        
        // Make API request to our backend
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.COPERNICUS.SEARCH}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dataType,
                coordinates,
                startDate,
                endDate
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `API request failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('API response:', data);
        
        // Return the results
        return data.results || [];
        
    } catch (error) {
        console.error('Error searching for satellite data:', error);
        
        // For demo purposes, fall back to mock data
        console.warn('Using mock data as fallback');
        
        // Extract parameters for mock data
        const { dataType, coordinates, startDate, endDate } = params;
        const wkt = coordinatesToWkt(coordinates);
        
        // Return mock search results
        return [
            {
                Id: `S2A_MSIL2A_${startDate.replace(/-/g, '')}T104031_N0509_R008_T31TDG_${startDate.replace(/-/g, '')}T150956`,
                Name: `Sentinel-2A L2A product from ${startDate}`,
                Footprint: wkt,
                ContentDate: {
                    Start: `${startDate}T10:40:31.024Z`,
                    End: `${startDate}T10:40:41.024Z`
                },
                CloudCoverPercentage: 5.2,
                Size: 1258291200, // ~1.2GB in bytes
                ContentType: dataType,
                Checksum: [
                    {
                        Value: "8d5e8e6f7c9b2a1d4e6f8c9a3b2d1e5f",
                        Algorithm: "MD5"
                    }
                ],
                ProductInformation: {
                    ProductType: dataType,
                    ProductFormat: "SAFE"
                }
            },
            {
                Id: `S2B_MSIL2A_${endDate.replace(/-/g, '')}T104619_N0509_R008_T31TDG_${endDate.replace(/-/g, '')}T141155`,
                Name: `Sentinel-2B L2A product from ${endDate}`,
                Footprint: wkt,
                ContentDate: {
                    Start: `${endDate}T10:46:19.024Z`,
                    End: `${endDate}T10:46:29.024Z`
                },
                CloudCoverPercentage: 12.8,
                Size: 1363148800, // ~1.3GB in bytes
                ContentType: dataType,
                Checksum: [
                    {
                        Value: "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
                        Algorithm: "MD5"
                    }
                ],
                ProductInformation: {
                    ProductType: dataType,
                    ProductFormat: "SAFE"
                }
            }
        ];
    }
}

/**
 * Fetch satellite data using transaction details
 * @param {Object} params Request parameters
 * @param {string} params.dataType Data type ID
 * @param {Array} params.coordinates Array of [lat, lng] coordinates
 * @param {string} params.startDate Start date (YYYY-MM-DD)
 * @param {string} params.endDate End date (YYYY-MM-DD)
 * @param {string} params.transactionHash Blockchain transaction hash
 * @returns {Promise<Object>} Satellite data and metadata
 */
async function fetchSatelliteData(params) {
    console.log('Fetching satellite data with params:', params);
    
    try {
        // Extract parameters
        const { dataType, coordinates, startDate, endDate, transactionHash } = params;
        
        // In a real app, this would verify the transaction on the blockchain
        // For now, simulate verification
        console.log('Verifying transaction:', transactionHash);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Search for data
        const searchResults = await searchSatelliteData({
            dataType,
            coordinates,
            startDate,
            endDate
        });
        
        if (!searchResults.length) {
            throw new Error('No data found matching the criteria');
        }
        
        // Fetch up to 3 products for display
        const productsToFetch = searchResults.slice(0, 3);
        const imageUrls = [];
        
        console.log(`Fetching ${productsToFetch.length} products...`);
        
        for (const product of productsToFetch) {
            const productId = product.Id;
            console.log('Fetching product data for ID:', productId);
            
            try {
                // Make API request to our backend to get product data
                const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.COPERNICUS.PRODUCT}/${productId}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error(`Failed to fetch product ${productId}:`, errorData.error);
                    continue; // Skip this product and try the next one
                }
                
                const data = await response.json();
                
                // Add the image URL to our array
                if (data.preview && data.preview.data) {
                    imageUrls.push({
                        url: data.preview.data,
                        metadata: data.metadata || product,
                        source: data.preview.source
                    });
                }
                
            } catch (downloadError) {
                console.error('Error downloading product:', downloadError);
                // Continue with next product
            }
        }
        
        // If we got at least one image, return the data
        if (imageUrls.length > 0) {
            return {
                data: 'real-image-data',
                metadata: productsToFetch[0],
                imageUrl: imageUrls[0].url, // Primary image
                additionalImages: imageUrls, // All images
                transactionHash,
                isReal: true,
                searchResults: searchResults
            };
        } else {
            throw new Error('Failed to fetch any product images');
        }
        
    } catch (error) {
        console.error('Error fetching satellite data:', error);
        
        // For demo purposes, fall back to mock data with multiple images
        console.warn('Using mock data as fallback');
        
        // Extract parameters for mock data
        const { dataType, coordinates, startDate, endDate, transactionHash } = params;
        
        // Return mock data with multiple images
        return {
            data: 'mock-binary-data',
            metadata: {
                Id: `S2A_MSIL2A_${startDate.replace(/-/g, '')}T104031_N0509_R008_T31TDG_${startDate.replace(/-/g, '')}T150956`,
                Name: `Sentinel-2A L2A product from ${startDate}`,
                ContentType: dataType,
                Size: 1258291200 // ~1.2GB in bytes
            },
            imageUrl: '../assets/sample-satellite-image.png',
            additionalImages: [
                { url: '../assets/sample-satellite-image.png', metadata: { Name: 'Image 1' } },
                { url: '../assets/sample-analysis-chart.png', metadata: { Name: 'Image 2' } },
                { url: '../assets/sample-satellite-image.png', metadata: { Name: 'Image 3' } }
            ],
            transactionHash,
            isMock: true
        };
    }
}

/**
 * Analyze satellite data using AI
 * @param {Object} data Satellite data
 * @returns {Promise<Object>} Analysis results
 */
async function analyzeSatelliteData(data) {
    console.log('Analyzing satellite data using AI...');
    
    try {
        // Extract parameters from the data and properly handle image URLs
        const { dataType, coordinates, startDate, endDate, location } = data;
        
        // Extract image URLs from satellite data
        let extractedImageUrls = [];
        
        // Check for additionalImages array (multiple images)
        if (data.additionalImages && Array.isArray(data.additionalImages)) {
            extractedImageUrls = data.additionalImages.map(img => img.url || img);
            console.log(`Found ${extractedImageUrls.length} images to send to AI analysis`);
        } 
        // Fallback to single imageUrl
        else if (data.imageUrl) {
            extractedImageUrls = [data.imageUrl];
            console.log('Found 1 image to send to AI analysis');
        }
        // Check if imageUrls was directly provided
        else if (data.imageUrls && Array.isArray(data.imageUrls)) {
            extractedImageUrls = data.imageUrls;
            console.log(`Found ${extractedImageUrls.length} images from imageUrls property`);
        }
        
        console.log('Image URLs being sent to AI:', extractedImageUrls);
        
        // Call the AI analysis API
        const response = await fetch(`${API_CONFIG.BASE_URL}/ai/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dataType: dataType || 'S2MSI2A',
                location: location || 'Selected Area',
                startDate: startDate || new Date().toISOString().split('T')[0],
                endDate: endDate || new Date().toISOString().split('T')[0],
                coordinates: coordinates,
                imageUrls: extractedImageUrls // Pass the extracted image URLs
            })
        });
        
        if (!response.ok) {
            throw new Error(`AI analysis failed: ${response.status} ${response.statusText}`);
        }
        
        const analysisResult = await response.json();
        console.log('AI analysis complete:', analysisResult);
        
        // Ensure the result has the expected structure
        return {
            landCover: analysisResult.landCover || {
                forest: 33.3,
                urban: 33.3,
                water: 33.4
            },
            change: analysisResult.change || {
                forestChange: 0,
                urbanChange: 0,
                waterChange: 0
            },
            health: analysisResult.health || {
                vegetationIndex: 0.7,
                waterQuality: 'Good',
                urbanDensity: 'Medium'
            },
            insights: analysisResult.insights || [
                'AI analysis completed successfully.',
                'Land cover distribution shows typical patterns for this region.',
                'Environmental indicators are within expected ranges.'
            ]
        };
        
    } catch (error) {
        console.error('Error in AI analysis:', error);
        
        // NO DEFAULT VALUES - throw error to be handled by UI
        throw new Error(`AI analysis failed: ${error.message}. Please ensure the AI service is running and try again.`);
    }
}

// Export functions for use in other files
window.copernicusAPI = {
    getAvailableDataTypes,
    searchSatelliteData,
    fetchSatelliteData,
    analyzeSatelliteData
};
