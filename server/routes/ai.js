/**
 * AI Routes
 * Defines API endpoints for AI features
 */

const express = require('express');
const router = express.Router();
const aiController = require('../controllers/ai');

// Analyze satellite data
router.post('/analyze', aiController.analyzeSatelliteData);

// Generate chat response
router.post('/chat', aiController.generateChatResponse);

// Geocode location
router.get('/geocode', aiController.geocodeLocation);

module.exports = router;
