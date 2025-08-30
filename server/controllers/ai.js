/**
 * AI Controller
 * Handles HTTP requests for AI analysis and chat features
 */

const aiService = require('../services/ai');

/**
 * Analyze satellite data
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const analyzeSatelliteData = async (req, res) => {
  try {
    const { dataType, location, startDate, endDate, coordinates, imageUrls } = req.body;
    
    // Validate required parameters
    if (!dataType || !startDate || !endDate) {
      return res.status(400).json({ 
        error: 'Missing required parameters: dataType, startDate, endDate' 
      });
    }
    
    // Call AI service to analyze data
    const analysisResults = await aiService.analyzeSatelliteData({
      dataType,
      location,
      startDate,
      endDate,
      coordinates,
      imageUrls
    });
    
    // Return analysis results
    res.json(analysisResults);
    
  } catch (error) {
    console.error('Error in analyzeSatelliteData controller:', error);
    res.status(500).json({ 
      error: error.message || 'Failed to analyze satellite data' 
    });
  }
};

/**
 * Generate chat response
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const generateChatResponse = async (req, res) => {
  try {
    const { 
      query, 
      dataType, 
      location, 
      coordinates, 
      startDate, 
      endDate, 
      conversationHistory,
      userApplication 
    } = req.body;
    
    // Validate required parameters
    if (!query) {
      return res.status(400).json({ 
        error: 'Missing required parameter: query' 
      });
    }
    
    // Call AI service to generate response
    const response = await aiService.generateChatResponse({
      query,
      dataType,
      location,
      coordinates,
      startDate,
      endDate,
      conversationHistory,
      userApplication
    });
    
    // Return chat response
    res.json({ response });
    
  } catch (error) {
    console.error('Error in generateChatResponse controller:', error);
    res.status(500).json({ 
      error: error.message || 'Failed to generate chat response' 
    });
  }
};

/**
 * Geocode location
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const geocodeLocation = async (req, res) => {
  try {
    const { location } = req.query;
    
    // Validate required parameters
    if (!location) {
      return res.status(400).json({ 
        error: 'Missing required parameter: location' 
      });
    }
    
    // Call AI service to geocode location
    const result = await aiService.geocodeLocation(location);
    
    // Return geocoding result
    res.json(result);
    
  } catch (error) {
    console.error('Error in geocodeLocation controller:', error);
    res.status(500).json({ 
      error: error.message || 'Failed to geocode location' 
    });
  }
};

module.exports = {
  analyzeSatelliteData,
  generateChatResponse,
  geocodeLocation
};
