/**
 * Copernicus API routes
 */

const express = require('express');
const router = express.Router();
const copernicusController = require('../controllers/copernicus');

/**
 * @route POST /api/copernicus/search
 * @desc Search for satellite data
 * @access Public
 */
router.post('/search', copernicusController.searchSatelliteData);

/**
 * @route GET /api/copernicus/product/:productId/preview
 * @desc Get product preview image
 * @access Public
 */
router.get('/product/:productId/preview', copernicusController.getProductPreview);

/**
 * @route GET /api/copernicus/product/:productId/metadata
 * @desc Get product metadata
 * @access Public
 */
router.get('/product/:productId/metadata', copernicusController.getProductMetadata);

/**
 * @route GET /api/copernicus/product/:productId
 * @desc Get product data with preview and metadata
 * @access Public
 */
router.get('/product/:productId', copernicusController.getProductData);

module.exports = router;
