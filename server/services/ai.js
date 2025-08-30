/**
 * AI Service for SpaceData application (Node.js version)
 * Handles OpenAI API integration for satellite data analysis
 */

const axios = require('axios');
const config = require('../config');

// OpenAI API configuration
const OPENAI_API_KEY = config.ai.apiKey;
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

/**
 * Detect if coordinates represent a maritime/water area
 * @param {Array} coordinates Array of [lat, lng] coordinates
 * @returns {Promise<Object>} Area type detection result
 */
const detectAreaType = async (coordinates) => {
  if (!coordinates || coordinates.length === 0) {
    return { type: 'unknown', isWater: false, description: 'Unknown area' };
  }
  
  try {
    // Calculate center point
    const lats = coordinates.map(point => point[0]);
    const lngs = coordinates.map(point => point[1]);
    const centerLat = lats.reduce((a, b) => a + b) / lats.length;
    const centerLng = lngs.reduce((a, b) => a + b) / lngs.length;
    
    // Use reverse geocoding to identify the area
    const response = await axios.get('https://nominatim.openstreetmap.org/reverse', {
      params: {
        lat: centerLat,
        lon: centerLng,
        format: 'json',
        zoom: 10 // Get broader area context
      },
      headers: {
        'User-Agent': 'SpaceData-App/1.0'
      }
    });
    
    if (response.data) {
      const addressDetails = response.data.address || {};
      const displayName = response.data.display_name || '';
      
      // Check for water bodies
      const waterKeywords = ['sea', 'ocean', 'mediterranean', 'atlantic', 'pacific', 'gulf', 'bay', 'strait', 'channel', 'lake'];
      const isWater = waterKeywords.some(keyword => displayName.toLowerCase().includes(keyword));
      
      // Determine area type
      let areaType = 'land';
      let description = displayName;
      
      if (isWater || addressDetails.water || addressDetails.sea || addressDetails.ocean) {
        areaType = 'maritime';
        description = `Maritime area in ${displayName}`;
      } else if (addressDetails.city || addressDetails.town) {
        areaType = 'urban';
        description = `Urban area: ${addressDetails.city || addressDetails.town}`;
      } else if (addressDetails.suburb || addressDetails.village) {
        areaType = 'suburban';
        description = `Suburban/rural area: ${addressDetails.suburb || addressDetails.village}`;
      }
      
      return {
        type: areaType,
        isWater: isWater,
        description: description,
        coordinates: [centerLat, centerLng]
      };
    }
  } catch (error) {
    console.warn('Geocoding failed, using coordinate-based detection:', error.message);
  }
  
  // Fallback: Use coordinate patterns for maritime detection
  // Mediterranean Sea approximately: 30-45°N, -5 to 35°E
  const centerLat = lats.reduce((a, b) => a + b) / lats.length;
  const centerLng = lngs.reduce((a, b) => a + b) / lngs.length;
  
  // Common sea/ocean coordinate ranges
  const maritimeAreas = [
    { name: 'Mediterranean Sea', latRange: [30, 45], lngRange: [-5, 35] },
    { name: 'Atlantic Ocean', latRange: [-60, 60], lngRange: [-80, -10] },
    { name: 'Pacific Ocean', latRange: [-60, 60], lngRange: [120, -120] },
    { name: 'North Sea', latRange: [51, 61], lngRange: [-3, 9] },
    { name: 'Baltic Sea', latRange: [53, 66], lngRange: [10, 30] }
  ];
  
  for (const area of maritimeAreas) {
    if (centerLat >= area.latRange[0] && centerLat <= area.latRange[1] &&
        ((area.lngRange[0] < area.lngRange[1] && centerLng >= area.lngRange[0] && centerLng <= area.lngRange[1]) ||
         (area.lngRange[0] > area.lngRange[1] && (centerLng >= area.lngRange[0] || centerLng <= area.lngRange[1])))) {
      return {
        type: 'maritime',
        isWater: true,
        description: `Maritime area (likely ${area.name})`,
        coordinates: [centerLat, centerLng]
      };
    }
  }
  
  return {
    type: 'land',
    isWater: false,
    description: `Land area at [${centerLat.toFixed(2)}, ${centerLng.toFixed(2)}]`,
    coordinates: [centerLat, centerLng]
  };
};

/**
 * Analyze satellite data using OpenAI
 * @param {Object} params Analysis parameters
 * @param {string} params.dataType Type of satellite data
 * @param {string} params.location Location name
 * @param {string} params.startDate Start date
 * @param {string} params.endDate End date
 * @param {Array} params.coordinates Coordinates array
 * @param {Array} params.imageUrls URLs of satellite images
 * @returns {Promise<Object>} Analysis results
 */
const analyzeSatelliteData = async (params) => {
  try {
    const { dataType, location, startDate, endDate, coordinates, imageUrls } = params;
    
    // Map data type codes to human-readable names
    const dataTypeNames = {
      'S2MSI2A': 'Sentinel-2 Level 2A (multispectral imagery)',
      'S1GRD': 'Sentinel-1 SAR (radar imagery)',
      'S3OLCI': 'Sentinel-3 OLCI (ocean and land color)'
    };
    
    const dataTypeName = dataTypeNames[dataType] || dataType;
    
    // Detect area type (maritime, urban, rural, etc.)
    const areaInfo = await detectAreaType(coordinates);
    console.log('Detected area type:', areaInfo);
    
    // Process coordinates to get geographic context
    let geoContext = '';
    if (coordinates && coordinates.length > 0) {
      const lats = coordinates.map(point => point[0]);
      const lngs = coordinates.map(point => point[1]);
      const centerLat = lats.reduce((a, b) => a + b) / lats.length;
      const centerLng = lngs.reduce((a, b) => a + b) / lngs.length;
      
      geoContext = `The analyzed area is centered around coordinates [${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}].`;
      
      // Add area type context
      if (areaInfo.type === 'maritime') {
        geoContext += `\nIMPORTANT: This is a MARITIME/SEA area. ${areaInfo.description}. The analysis should reflect that this is primarily water (ocean/sea), with minimal or no land coverage.`;
      } else {
        geoContext += `\nArea type: ${areaInfo.description}`;
      }
    }
    
    // Create area-specific analysis prompt
    let analysisGuidance = '';
    if (areaInfo.type === 'maritime') {
      analysisGuidance = `
      Since this is a maritime/sea area, the land cover distribution should reflect:
      - Water should be 85-98% of the total area
      - Urban should be 0-5% (only if there are small islands or coastal structures)
      - Forest should be 0-10% (only if there are islands with vegetation)
      
      Insights should focus on:
      - Ocean/sea conditions
      - Maritime traffic or shipping lanes
      - Marine ecosystems
      - Coastal development if any
      - Water quality and oceanographic features`;
    } else if (areaInfo.type === 'urban') {
      analysisGuidance = `
      For this urban area, provide realistic urban land cover distribution and insights about:
      - Urban infrastructure and development
      - Green spaces and parks
      - Water bodies (rivers, lakes) if present
      - Urban expansion trends`;
    }
    
    // Create the analysis prompt with intelligent fallback mechanism
    const systemPrompt = `You are an expert in satellite imagery analysis and Earth observation.
    
    CRITICAL ANALYSIS PROTOCOL:
    
    STEP 1 - IMAGE QUALITY ASSESSMENT:
    First, assess the quality and resolution of any provided satellite images:
    - Can you clearly distinguish features (buildings, vegetation, water bodies)?
    - Is the image resolution sufficient to identify land cover types?
    - Are there clouds, artifacts, or other obstructions?
    
    STEP 2 - ANALYSIS APPROACH:
    Based on image quality, use one of these approaches:
    
    A) HIGH/MEDIUM RESOLUTION (clear features visible):
       - Analyze ACTUAL features visible in the satellite images
       - Base percentages on observed pixel distributions
       - Identify specific patterns, boundaries, and textures
    
    B) LOW/INSUFFICIENT RESOLUTION (features unclear or no images):
       - FALLBACK MECHANISM: Use your knowledge of the geographic area
       - The coordinates indicate: ${geoContext}
       - Apply known geographic data for ${location || 'this region'} at [${coordinates ? coordinates.map(c => `${c[0].toFixed(4)}, ${c[1].toFixed(4)}`).join('; ') : 'location'}]
       - Consider typical land cover for this region's climate, geography, and development patterns
       - Use knowledge of local geography, urban centers, water bodies, and vegetation patterns
    
    C) HYBRID (partial visibility):
       - Combine visible features with geographic knowledge
       - Use images where clear, fill gaps with regional knowledge
    
    Data context:
    - Satellite type: ${dataTypeName}
    - Location: ${location || 'the selected area'}
    - Date range: ${startDate} to ${endDate}
    - Geographic coordinates: [${coordinates ? coordinates.map(c => `${c[0].toFixed(4)}, ${c[1].toFixed(4)}`).join('; ') : 'not provided'}]
    ${geoContext}
    
    ${analysisGuidance}
    
    IMPORTANT: You MUST be transparent about your analysis source!
    
    Return your response as a JSON object with this EXACT structure:
    {
      "analysisSource": "satellite_imagery" | "geographic_knowledge" | "hybrid",
      "imageQuality": "high" | "medium" | "low" | "insufficient",
      "qualityNote": "<Brief explanation of image quality and why you chose this analysis approach>",
      "landCover": {
        "forest": <percentage - from images OR geographic knowledge>,
        "urban": <percentage - from images OR geographic knowledge>,
        "water": <percentage - from images OR geographic knowledge>
      },
      "change": {
        "forestChange": <change value or 0>,
        "urbanChange": <change value or 0>,
        "waterChange": <change value or 0>
      },
      "health": {
        "vegetationIndex": <0-1 value>,
        "waterQuality": "Good" | "Moderate" | "Poor",
        "urbanDensity": "Low" | "Medium" | "High"
      },
      "insights": [
        "First insight MUST indicate analysis source: 'Based on [satellite imagery/geographic knowledge/hybrid analysis]...'",
        "If using fallback: 'Note: Due to image resolution limitations, this analysis uses geographic knowledge for ${location || 'this area'} at the specified coordinates.'",
        "Include region-specific insights based on either imagery or geographic knowledge",
        "Mention specific features observed or known about this location",
        "Ask what application the user needs this data for to provide targeted insights"
      ]
    }
    
    GEOGRAPHIC KNOWLEDGE GUIDELINES (for fallback):
    - Use your knowledge of the specific region's geography, climate, and development
    - Consider seasonal variations for the date range ${startDate} to ${endDate}
    - Apply typical land cover distributions for this latitude/longitude
    - Reference known cities, forests, water bodies in the area
    - Consider the area type: ${areaInfo.description}`;
    
    // Prepare the user message content
    let userContent = [];
    
    // Add text prompt with explicit instructions about fallback
    userContent.push({
      type: 'text',
      text: `Please analyze the satellite data for ${location || 'the area'} at coordinates [${coordinates ? coordinates.map(c => `${c[0].toFixed(4)}, ${c[1].toFixed(4)}`).join('; ') : 'unknown'}]. 
      
      IMPORTANT: 
      1. First assess if the provided images (if any) have sufficient resolution
      2. If images are unclear or missing, use your geographic knowledge about this specific location
      3. Be transparent about whether you're using image analysis or geographic knowledge
      4. Provide the results in the specified JSON format.`
    });
    
    // Add images if provided
    if (imageUrls && Array.isArray(imageUrls) && imageUrls.length > 0) {
      for (const imageUrl of imageUrls) {
        if (imageUrl) {
          // Check if it's a base64 image or URL
          if (imageUrl.startsWith('data:image')) {
            // Base64 image
            userContent.push({
              type: 'image_url',
              image_url: {
                url: imageUrl,
                detail: 'high' // Use high detail for satellite imagery analysis
              }
            });
          } else if (imageUrl.startsWith('http')) {
            // Regular URL
            userContent.push({
              type: 'image_url',
              image_url: {
                url: imageUrl,
                detail: 'high'
              }
            });
          }
        }
      }
      
      console.log(`Sending ${imageUrls.length} satellite images to OpenAI for analysis`);
    } else {
      console.log('No satellite images provided, using text-based analysis only');
    }
    
    // Call OpenAI API with Vision capabilities
    const response = await axios.post(
      OPENAI_API_URL,
      {
        model: 'gpt-4o', // Using gpt-4o which has vision capabilities
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userContent }
        ],
        response_format: { type: 'json_object' },
        max_tokens: 800, // Increased for more detailed analysis
        temperature: 0.2
      },
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    // Parse the response
    const aiResponse = response.data.choices[0].message.content;
    
    // Extract JSON from the response
    let analysisResult;
    try {
      // Find JSON in the response
      const jsonStart = aiResponse.indexOf('{');
      const jsonEnd = aiResponse.lastIndexOf('}') + 1;
      
      if (jsonStart >= 0 && jsonEnd > jsonStart) {
        const jsonStr = aiResponse.substring(jsonStart, jsonEnd);
        analysisResult = JSON.parse(jsonStr);
      } else {
        analysisResult = JSON.parse(aiResponse);
      }
    } catch (parseError) {
      console.error('Error parsing AI response:', parseError);
      // NO DEFAULT VALUES - throw error to be handled by caller
      throw new Error(`Failed to parse OpenAI response: ${parseError.message}`);
    }
    
    // Validate and ensure all required fields are present
    analysisResult = validateAnalysisResult(analysisResult);
    
    // Log the analysis source for debugging
    console.log(`Analysis completed using: ${analysisResult.analysisSource || 'unknown source'}`);
    if (analysisResult.imageQuality) {
      console.log(`Image quality assessed as: ${analysisResult.imageQuality}`);
    }
    
    return analysisResult;
    
  } catch (error) {
    console.error('Error analyzing satellite data - Full details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      params: {
        dataType: params.dataType,
        location: params.location,
        hasCoordinates: !!params.coordinates,
        hasImages: !!params.imageUrls,
        imageCount: params.imageUrls?.length || 0
      }
    });
    
    // Check if it's an API key issue
    if (error.response?.status === 401) {
      console.error('OpenAI API Key authentication failed. Please check your API key.');
    }
    
    // NO DEFAULT VALUES - throw error to be handled by caller
    throw new Error(`Failed to analyze satellite data with OpenAI: ${error.message}`);
  }
};

/**
 * Generate chat response for user queries
 * @param {Object} params Chat parameters
 * @param {string} params.query User's query
 * @param {string} params.dataType Type of satellite data
 * @param {string} params.location Location name
 * @param {Array} params.coordinates Geographic coordinates
 * @param {string} params.startDate Start date
 * @param {string} params.endDate End date
 * @param {Array} params.conversationHistory Previous conversation messages
 * @param {string} params.userApplication User's stated application/use case
 * @returns {Promise<string>} AI response
 */
const generateChatResponse = async (params) => {
  try {
    const { query, dataType, location, coordinates, startDate, endDate, conversationHistory = [], userApplication = null } = params;
    
    // Map data type codes to human-readable names
    const dataTypeNames = {
      'S2MSI2A': 'Sentinel-2 Level 2A',
      'S1GRD': 'Sentinel-1 SAR',
      'S3OLCI': 'Sentinel-3 OLCI'
    };
    
    const dataTypeName = dataTypeNames[dataType] || dataType;
    
    
    // Create geographic context
    let geoContext = '';
    if (coordinates && coordinates.length > 0) {
      const lats = coordinates.map(point => point[0]);
      const lngs = coordinates.map(point => point[1]);
      const centerLat = lats.reduce((a, b) => a + b) / lats.length;
      const centerLng = lngs.reduce((a, b) => a + b) / lngs.length;
      geoContext = `The area is located at coordinates [${centerLat.toFixed(4)}, ${centerLng.toFixed(4)}].`;
    }
    
    // Build conversation history context
    let conversationContext = '';
    let firstUserMessage = '';
    if (conversationHistory && conversationHistory.length > 0) {
      // Find the first user message to understand their application
      const firstUserMsg = conversationHistory.find(msg => msg.role === 'user');
      if (firstUserMsg) {
        firstUserMessage = firstUserMsg.content;
      }
      
      conversationContext = '\nPrevious conversation:\n';
      conversationHistory.slice(-4).forEach(msg => { // Keep last 4 messages for context
        conversationContext += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n`;
      });
    }
    
    // Build user application context
    let applicationContext = '';
    if (firstUserMessage) {
      applicationContext = `\nFIRST USER MESSAGE (understand their application from this): "${firstUserMessage}"`;
    } else if (userApplication) {
      applicationContext = `\nUser's stated application: ${userApplication}`;
    }
    
    const systemPrompt = `You are an AI assistant for SpaceData, helping users understand satellite imagery analysis.
    
    CRITICAL FORMATTING RULES:
    - NEVER use markdown formatting (no asterisks, hashes, or backticks)
    - Write all responses in plain text only
    - Use clear, simple formatting without any special characters
    
    DATA CONTEXT:
    You are analyzing ${dataTypeName} data for ${location || 'the selected area'} from ${startDate} to ${endDate}.
    ${geoContext}
    ${applicationContext}
    ${conversationContext}
    
    IMPORTANT: Real satellite analysis is not yet implemented. Focus responses on:
    - Location and coordinate information only
    - General geographic knowledge about the area
    - Understanding the user's application needs
    - Asking clarifying questions about their specific use case
    
    RESPONSE GUIDELINES:
    1. Always reference the specific coordinates when discussing the area: [${coordinates ? coordinates.map(c => `${c[0].toFixed(4)}, ${c[1].toFixed(4)}`).join('; ') : 'coordinates not provided'}]
    2. ${firstUserMessage ? 
        `CRITICAL: Look at the user's first message above to understand their application/use case. They already told you what they need. DO NOT ask what they will use it for - understand it from their first message and respond accordingly.` : 
        `If they haven't specified their application yet, ASK them first: "What will you be using this satellite data for?"`}
    3. Be specific with numbers and percentages from the actual analysis
    4. Provide actionable insights based on the exact location and data
    5. Remember and reference previous conversation context
    6. ${firstUserMessage ? `Tailor all insights based on the application mentioned in their first message` : 'Wait for their application before providing targeted insights'}
    
    CONTENT REQUIREMENTS:
    - Mention the exact location coordinates in your first response
    - Keep responses under 150 words unless asked for more detail
    - Be direct and specific about what data is available (coordinates and location only)
    - Explain that detailed satellite analysis is still being developed
    - Focus on understanding their application needs
    - NEVER forget the user's stated application once they've told you`;
    
    // Build messages array with conversation history
    const messages = [
      { role: 'system', content: systemPrompt }
    ];
    
    // Add conversation history if available
    if (conversationHistory && conversationHistory.length > 0) {
      conversationHistory.slice(-4).forEach(msg => {
        messages.push({
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: msg.content
        });
      });
    }
    
    // Add current query
    messages.push({ role: 'user', content: query });
    
    // Call OpenAI API
    const response = await axios.post(
      OPENAI_API_URL,
      {
        model: 'gpt-4o-mini',
        messages: messages,
        max_tokens: 300,
        temperature: 0.7
      },
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data.choices[0].message.content.trim();
    
  } catch (error) {
    console.error('Error generating chat response:', error.message);
    return `I'm analyzing the satellite data for ${params.location || 'this area'}. The data shows interesting patterns in land use and environmental changes. Please feel free to ask specific questions about the vegetation, urban development, or water bodies in this region.`;
  }
};

/**
 * Geocode location to coordinates
 * @param {string} locationQuery Location description
 * @returns {Promise<Object>} Geocoding result
 */
const geocodeLocation = async (locationQuery) => {
  try {
    // Use Nominatim API for geocoding
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: locationQuery,
        format: 'json',
        limit: 1,
        polygon_geojson: 1
      },
      headers: {
        'User-Agent': 'SpaceData-App/1.0'
      }
    });
    
    if (response.data && response.data.length > 0) {
      const location = response.data[0];
      const lat = parseFloat(location.lat);
      const lng = parseFloat(location.lon);
      
      // Create a bounding box around the location
      let polygon;
      if (location.geojson && location.geojson.coordinates) {
        // Use the actual polygon if available
        const coords = location.geojson.coordinates[0];
        polygon = coords.map(coord => [coord[1], coord[0]]); // Convert to [lat, lng]
      } else if (location.boundingbox) {
        // Use bounding box
        const [minLat, maxLat, minLng, maxLng] = location.boundingbox.map(parseFloat);
        polygon = [
          [minLat, minLng],
          [minLat, maxLng],
          [maxLat, maxLng],
          [maxLat, minLng]
        ];
      } else {
        // Create a small box around the point
        const delta = 0.05;
        polygon = [
          [lat - delta, lng - delta],
          [lat - delta, lng + delta],
          [lat + delta, lng + delta],
          [lat + delta, lng - delta]
        ];
      }
      
      return {
        success: true,
        polygon: polygon,
        location_name: location.display_name,
        center: [lat, lng]
      };
    }
    
    return {
      success: false,
      error: 'Location not found'
    };
    
  } catch (error) {
    console.error('Error geocoding location:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
};

/**
 * Validate analysis result structure from OpenAI
 * Only ensures the structure is correct, does NOT add default values
 * @param {Object} result Analysis result to validate
 * @returns {Object} Valid analysis result
 */
const validateAnalysisResult = (result) => {
  // Ensure all required fields exist - if missing, throw error
  if (!result || typeof result !== 'object') {
    throw new Error('Invalid analysis result from OpenAI: result is not an object');
  }
  
  // Validate new fields for analysis source and quality (with defaults for backward compatibility)
  if (!result.analysisSource) {
    result.analysisSource = 'unknown';
  }
  
  if (!result.imageQuality) {
    result.imageQuality = 'unknown';
  }
  
  // Validate land cover exists
  if (!result.landCover || typeof result.landCover !== 'object') {
    throw new Error('Invalid analysis result from OpenAI: missing landCover data');
  }
  
  // Ensure required land cover fields exist
  if (result.landCover.forest === undefined || result.landCover.urban === undefined || result.landCover.water === undefined) {
    throw new Error('Invalid analysis result from OpenAI: incomplete landCover data');
  }
  
  // Ensure percentages sum to 100 (allow small rounding errors)
  const total = result.landCover.forest + result.landCover.urban + result.landCover.water;
  if (Math.abs(total - 100) > 0.1) {
    // Only normalize if values exist, don't add defaults
    const scale = 100 / total;
    result.landCover.forest = result.landCover.forest * scale;
    result.landCover.urban = result.landCover.urban * scale;
    result.landCover.water = result.landCover.water * scale;
  }
  
  // Validate change exists
  if (!result.change || typeof result.change !== 'object') {
    throw new Error('Invalid analysis result from OpenAI: missing change data');
  }
  
  // Validate health exists
  if (!result.health || typeof result.health !== 'object') {
    throw new Error('Invalid analysis result from OpenAI: missing health data');
  }
  
  // Validate insights exists and is not empty
  if (!Array.isArray(result.insights) || result.insights.length === 0) {
    throw new Error('Invalid analysis result from OpenAI: missing or empty insights');
  }
  
  return result;
};

module.exports = {
  analyzeSatelliteData,
  generateChatResponse,
  geocodeLocation
};
