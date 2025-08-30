/**
 * Pricing module for SpaceData web application
 * Handles price calculation and Flare VRF integration for random variance
 */

// Data type base prices (in FLR)
const DATA_TYPE_PRICES = {
    'Sentinel-2 Level 2A': 10,
    'Sentinel-1 SAR': 15,
    'Sentinel-3 OLCI': 5
};

// Resolution multipliers
const RESOLUTION_MULTIPLIERS = {
    '10m': 1.5,  // High resolution
    '5-20m': 1.3, // Medium-high resolution
    '300m': 0.8   // Lower resolution
};

// AI analysis price multiplier
const AI_ANALYSIS_MULTIPLIER = 1.25; // 25% increase for AI analysis

// Network fee in FLR
const NETWORK_FEE = 0.1;

/**
 * Calculate area in square kilometers from polygon coordinates
 * @param {L.Polygon} polygon - Leaflet polygon object
 * @returns {number} - Area in square kilometers
 */
function calculateAreaInSqKm(polygon) {
    if (!polygon || !polygon.getLatLngs || !polygon.getLatLngs()[0] || polygon.getLatLngs()[0].length < 3) {
        return 1; // Default to 1 sq km if no valid polygon
    }
    
    try {
        // Calculate a simple area based on the bounding box
        // This is more reliable than geodesicArea which can be unpredictable
        const latlngs = polygon.getLatLngs()[0];
        
        // Find min/max lat/lng to create a bounding box
        let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
        
        for (const point of latlngs) {
            minLat = Math.min(minLat, point.lat);
            maxLat = Math.max(maxLat, point.lat);
            minLng = Math.min(minLng, point.lng);
            maxLng = Math.max(maxLng, point.lng);
        }
        
        // Calculate width and height in kilometers
        // Approximate conversion: 1 degree latitude = 111 km
        // 1 degree longitude = 111 km * cos(latitude)
        const avgLat = (minLat + maxLat) / 2;
        const heightKm = (maxLat - minLat) * 111;
        const widthKm = (maxLng - minLng) * 111 * Math.cos(avgLat * Math.PI / 180);
        
        // Calculate area and apply a factor to account for non-rectangular shapes
        const area = heightKm * widthKm * 0.8; // 0.8 factor to account for non-rectangular shapes
        
        console.log('Bounding box dimensions:', heightKm.toFixed(2), 'km x', widthKm.toFixed(2), 'km');
        console.log('Calculated area:', area.toFixed(2), 'sq km');
        
        return Math.max(1, area);
    } catch (error) {
        console.error('Error calculating area:', error);
        return 1; // Default to 1 sq km on error
    }
}

/**
 * Calculate base price based on selected options
 * @param {string} dataType - Selected data type
 * @param {L.Polygon} polygon - Selected area polygon
 * @param {boolean} aiAnalysisEnabled - Whether AI analysis is enabled
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {number} - Base price in FLR
 */
function calculateBasePrice(dataType, polygon, aiAnalysisEnabled, startDate, endDate) {
    // Get base price for data type
    const basePrice = DATA_TYPE_PRICES[dataType] || 10; // Default to 10 FLR if type not found
    
    // Get resolution multiplier
    let resolutionMultiplier = 1.0;
    if (dataType === 'Sentinel-2 Level 2A') {
        resolutionMultiplier = RESOLUTION_MULTIPLIERS['10m'];
    } else if (dataType === 'Sentinel-1 SAR') {
        resolutionMultiplier = RESOLUTION_MULTIPLIERS['5-20m'];
    } else if (dataType === 'Sentinel-3 OLCI') {
        resolutionMultiplier = RESOLUTION_MULTIPLIERS['300m'];
    }
    
    // Calculate area factor (price per 100 sq km)
    let area = 1;
    if (polygon) {
        area = calculateAreaInSqKm(polygon);
        console.log('Area calculated:', area.toFixed(2), 'sq km');
    }
    
    // More predictable area factor calculation:
    // 1 sq km = 0.5 factor (minimum)
    // 100 sq km = 1.0 factor
    // 1000 sq km = 10.0 factor
    // Linear scaling between these points
    const areaFactor = Math.max(0.5, area / 100);
    console.log('Area factor:', areaFactor.toFixed(2));
    
    // Calculate date range factor
    const dateRangeFactor = calculateDateRangeFactor(startDate, endDate);
    console.log('Date range factor:', dateRangeFactor);
    
    // Apply AI multiplier if enabled
    const aiMultiplier = aiAnalysisEnabled ? AI_ANALYSIS_MULTIPLIER : 1.0;
    
    // Calculate final base price
    let finalBasePrice = basePrice * resolutionMultiplier * areaFactor * dateRangeFactor * aiMultiplier;
    
    // Add network fee
    finalBasePrice += NETWORK_FEE;
    
    // Divide by 50,000 to make prices 100 times less
    finalBasePrice = finalBasePrice / 50000;
    
    // Round to 2 decimal places
    return Math.round(finalBasePrice * 100) / 100;
}

/**
 * Calculate price factor based on date range
 * @param {string} startDate - Start date (YYYY-MM-DD)
 * @param {string} endDate - End date (YYYY-MM-DD)
 * @returns {number} - Date range factor
 */
function calculateDateRangeFactor(startDate, endDate) {
    try {
        // Parse dates
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        // Calculate days difference
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 to include both start and end days
        
        // Calculate factor: 1.0 for 7 days, scales linearly
        // Minimum 0.5 (for 1 day), maximum 2.0 (for 30+ days)
        const factor = Math.max(0.5, Math.min(2.0, diffDays / 7));
        
        return factor;
    } catch (error) {
        console.error('Error calculating date range factor:', error);
        return 1.0; // Default factor on error
    }
}

/**
 * Generate a seed for randomization
 * @param {string} dataType - Selected data type
 * @param {L.Polygon} polygon - Selected area polygon
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {string} - Seed for randomization
 */
function generateSeed(dataType, polygon, startDate, endDate) {
    // Get coordinates as string
    let coordinatesString = "no-area";
    if (polygon && polygon.getLatLngs()[0].length > 0) {
        coordinatesString = polygon.getLatLngs()[0]
            .map(latLng => `${latLng.lat.toFixed(4)},${latLng.lng.toFixed(4)}`)
            .join(';');
    }
    
    // Create seed using parameters and current timestamp
    return `${dataType}-${coordinatesString}-${startDate}-${endDate}-${Date.now()}`;
}

/**
 * Apply random variance to base price using Flare VRF
 * @param {number} basePrice - Base price before randomization
 * @param {Object} params - Parameters for VRF request
 * @returns {Promise<number>} - Final price with randomization applied
 */
async function applyRandomVariance(basePrice, params) {
    try {
        // Request randomness from Flare VRF
        const vrfResult = await window.flareVRF.requestRandomness(params);
        
        // Get normalized random value (0-1 range)
        const random = vrfResult.normalizedValue;
        
        // Apply ±10% random factor
        const randomFactor = 0.9 + (random * 0.2); // Range: 0.9 to 1.1
        
        // Calculate final price: base price * random factor
        const finalPrice = basePrice * randomFactor;
        
        // Round to 2 decimal places
        return {
            finalPrice: Math.round(finalPrice * 100) / 100,
            randomFactor: Math.round((randomFactor - 1) * 100),
            vrfResult: vrfResult
        };
    } catch (error) {
        console.error('Error applying random variance:', error);
        
        // Fallback to a simple random factor if VRF fails
        const randomFactor = 0.95 + (Math.random() * 0.1); // Range: 0.95 to 1.05 (narrower range for fallback)
        const finalPrice = basePrice * randomFactor;
        
        return {
            finalPrice: Math.round(finalPrice * 100) / 100,
            randomFactor: Math.round((randomFactor - 1) * 100),
            isFallback: true
        };
    }
}

/**
 * Calculate final price with random variance
 * @param {string} dataType - Selected data type
 * @param {L.Polygon} polygon - Selected area polygon
 * @param {boolean} aiAnalysisEnabled - Whether AI analysis is enabled
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 * @returns {Promise<Object>} - Object containing base price, final price, and random factor
 */
async function calculateFinalPrice(dataType, polygon, aiAnalysisEnabled, startDate, endDate) {
    // Calculate base price
    const basePrice = calculateBasePrice(dataType, polygon, aiAnalysisEnabled, startDate, endDate);
    
    // Create params object for VRF request
    const params = {
        dataType,
        coordinates: polygon ? polygon.getLatLngs()[0].map(p => [p.lat, p.lng]) : [],
        startDate,
        endDate,
        aiAnalysisEnabled,
        timestamp: Date.now()
    };
    
    // Apply random variance using Flare VRF
    const { finalPrice, randomFactor, vrfResult, isFallback } = await applyRandomVariance(basePrice, params);
    
    return {
        basePrice: basePrice,
        finalPrice: finalPrice,
        randomFactor: randomFactor,
        vrfResult: vrfResult,
        isFallback: isFallback
    };
}

/**
 * Format price as string with FLR currency
 * @param {number} price - Price to format
 * @returns {string} - Formatted price string
 */
function formatPrice(price) {
    return price.toFixed(2) + ' FLR';
}

/**
 * Update price display in the UI
 * @param {string} dataType - Selected data type
 * @param {L.Polygon} polygon - Selected area polygon
 * @param {boolean} aiAnalysisEnabled - Whether AI analysis is enabled
 * @param {string} startDate - Start date
 * @param {string} endDate - End date
 */
async function updatePriceDisplay(dataType, polygon, aiAnalysisEnabled, startDate, endDate) {
    // Show loading state
    const priceElement = document.querySelector('.price-estimate-amount');
    const noteElement = document.querySelector('.price-estimate-note');
    const areaElement = document.querySelector('.area-size-display');
    
    if (priceElement) {
        priceElement.textContent = 'Calculating...';
    }
    
    if (noteElement) {
        noteElement.textContent = 'Requesting randomness from Flare VRF...';
    }
    
    if (areaElement) {
        areaElement.textContent = 'Calculating area...';
    }
    
    try {
        // Calculate area size
        let areaSize = 1; // Default 1 sq km
        if (polygon) {
            areaSize = calculateAreaInSqKm(polygon);
        }
        
        // Calculate price with VRF
        const priceInfo = await calculateFinalPrice(dataType, polygon, aiAnalysisEnabled, startDate, endDate);
        
        // Update price display
        if (priceElement) {
            priceElement.textContent = formatPrice(priceInfo.finalPrice);
        }
        
        // Update area size display
        if (areaElement) {
            areaElement.textContent = `Area: ${areaSize.toFixed(2)} sq km`;
        }
        
        // Update price note with actual variance
        if (noteElement) {
            const sign = priceInfo.randomFactor >= 0 ? '+' : '';
            let noteText = `Base price: ${formatPrice(priceInfo.basePrice)} with ${sign}${priceInfo.randomFactor}% variance from Flare VRF`;
            
            // Add fallback indicator if using fallback
            if (priceInfo.isFallback) {
                noteText += ' (using local fallback)';
            }
            
            noteElement.textContent = noteText;
        }
    } catch (error) {
        console.error('Error updating price display:', error);
        
        // Show error state
        if (priceElement) {
            priceElement.textContent = 'Error';
        }
        
        if (noteElement) {
            noteElement.textContent = 'Error calculating price. Please try again.';
        }
    }
}

// Export functions for use in other files
window.pricingFunctions = {
    calculateBasePrice,
    calculateFinalPrice,
    updatePriceDisplay,
    formatPrice
};
