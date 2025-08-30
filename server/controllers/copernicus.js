/**
 * Copernicus API controllers
 * Handles HTTP requests for Copernicus data
 */

const copernicusService = require('../services/copernicus');

/**
 * Search for satellite data
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const searchSatelliteData = async (req, res) => {
  try {
    // Extract parameters from request body
    const { dataType, coordinates, startDate, endDate } = req.body;
    
    // Validate required parameters
    if (!dataType) {
      return res.status(400).json({ error: 'Missing required parameter: dataType' });
    }
    
    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'Missing required parameters: startDate or endDate' });
    }
    
    // Search for satellite data
    const results = await copernicusService.searchSatelliteData({
      dataType,
      coordinates,
      startDate,
      endDate
    });
    
    // Return results
    res.json({ results });
  } catch (error) {
    console.error('Error in searchSatelliteData controller:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
};

/**
 * Get product preview image
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const getProductPreview = async (req, res) => {
  try {
    // Extract product ID from request parameters
    const { productId } = req.params;
    
    // Validate required parameters
    if (!productId) {
      return res.status(400).json({ error: 'Missing required parameter: productId' });
    }
    
    // Get product preview
    const preview = await copernicusService.getProductPreview(productId);
    
    // Set content type header
    res.set('Content-Type', preview.contentType);
    
    // Return preview image
    res.send(preview.data);
  } catch (error) {
    console.error('Error in getProductPreview controller:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
};

/**
 * Get product metadata
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const getProductMetadata = async (req, res) => {
  try {
    // Extract product ID from request parameters
    const { productId } = req.params;
    
    // Validate required parameters
    if (!productId) {
      return res.status(400).json({ error: 'Missing required parameter: productId' });
    }
    
    // Get product metadata
    const metadata = await copernicusService.getProductMetadata(productId);
    
    // Return metadata
    res.json({ metadata });
  } catch (error) {
    console.error('Error in getProductMetadata controller:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
};

/**
 * Get product data with preview and metadata
 * @param {Object} req Express request object
 * @param {Object} res Express response object
 */
const getProductData = async (req, res) => {
  try {
    // Extract product ID from request parameters
    const { productId } = req.params;
    
    // Validate required parameters
    if (!productId) {
      return res.status(400).json({ error: 'Missing required parameter: productId' });
    }
    
    // Get product metadata
    const metadata = await copernicusService.getProductMetadata(productId);
    
    // Get product preview
    let preview = null;
    let previewError = null;
    
    try {
      preview = await copernicusService.getProductPreview(productId);
    } catch (error) {
      previewError = error.message;
    }
    
    // Convert preview to base64 if available
    let previewData = null;
    if (preview && preview.data) {
      const base64 = Buffer.from(preview.data).toString('base64');
      previewData = `data:${preview.contentType};base64,${base64}`;
    }
    
    // Return data
    res.json({
      metadata,
      preview: {
        data: previewData,
        source: preview?.source,
        error: previewError
      }
    });
  } catch (error) {
    console.error('Error in getProductData controller:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
};

module.exports = {
  searchSatelliteData,
  getProductPreview,
  getProductMetadata,
  getProductData
};
