/**
 * Blockchain Routes
 * Defines API endpoints for blockchain-related operations
 */

const express = require('express');
const router = express.Router();
const blockchainController = require('../controllers/blockchain');
const axios = require('axios');

// Python backend base URL
const PYTHON_BACKEND_URL = 'http://localhost:5000';

// GET /api/blockchain/config - Get blockchain configuration
router.get('/config', blockchainController.getBlockchainConfig);

// POST /api/blockchain/verify - Verify blockchain attestation
router.post('/verify', blockchainController.verifyAttestation);

// POST /api/blockchain/purchase - Purchase satellite data
router.post('/purchase', blockchainController.purchaseData);

// Proxy routes to Python backend for FDC/DA layer operations

// POST /api/blockchain/request-attestation - Proxy to Python backend
router.post('/request-attestation', async (req, res) => {
    try {
        const response = await axios.post(
            `${PYTHON_BACKEND_URL}/api/blockchain/request-attestation`,
            req.body,
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
        res.json(response.data);
    } catch (error) {
        console.error('Error proxying request-attestation:', error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ 
                error: 'Failed to connect to Python backend',
                details: error.message 
            });
        }
    }
});

// GET /api/blockchain/fetch-attestation/:request_id - Proxy to Python backend
router.get('/fetch-attestation/:request_id', async (req, res) => {
    try {
        const response = await axios.get(
            `${PYTHON_BACKEND_URL}/api/blockchain/fetch-attestation/${req.params.request_id}`
        );
        res.json(response.data);
    } catch (error) {
        console.error('Error proxying fetch-attestation:', error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ 
                error: 'Failed to connect to Python backend',
                details: error.message 
            });
        }
    }
});

// POST /api/blockchain/verify-attestation - Proxy to Python backend
router.post('/verify-attestation', async (req, res) => {
    try {
        const response = await axios.post(
            `${PYTHON_BACKEND_URL}/api/blockchain/verify-attestation`,
            req.body,
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
        res.json(response.data);
    } catch (error) {
        console.error('Error proxying verify-attestation:', error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ 
                error: 'Failed to connect to Python backend',
                details: error.message 
            });
        }
    }
});

// POST /api/blockchain/deliver-data - Proxy to Python backend
router.post('/deliver-data', async (req, res) => {
    try {
        const response = await axios.post(
            `${PYTHON_BACKEND_URL}/api/blockchain/deliver-data`,
            req.body,
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
        res.json(response.data);
    } catch (error) {
        console.error('Error proxying deliver-data:', error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ 
                error: 'Failed to connect to Python backend',
                details: error.message 
            });
        }
    }
});

// POST /api/blockchain/generate-request-id - Proxy to Python backend
router.post('/generate-request-id', async (req, res) => {
    try {
        const response = await axios.post(
            `${PYTHON_BACKEND_URL}/api/blockchain/generate-request-id`,
            req.body,
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
        res.json(response.data);
    } catch (error) {
        console.error('Error proxying generate-request-id:', error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ 
                error: 'Failed to connect to Python backend',
                details: error.message 
            });
        }
    }
});

module.exports = router;
