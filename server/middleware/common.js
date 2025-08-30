/**
 * Common middleware for Express server
 */

const cors = require('cors');
const morgan = require('morgan');
const express = require('express');

/**
 * Apply common middleware to Express app
 * @param {Object} app Express app
 */
const applyCommonMiddleware = (app) => {
  // Enable CORS for all routes with specific configuration for development
  app.use(cors({
    origin: ['http://localhost:8080', 'http://localhost:3000', 'http://localhost:19006', 'http://127.0.0.1:19006'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
  }));
  
  // Parse JSON request bodies (increase limit to handle base64 images)
  app.use(express.json({ limit: '10mb' }));
  
  // Parse URL-encoded request bodies
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));
  
  // HTTP request logging
  app.use(morgan('dev'));
  
  // Add request timestamp
  app.use((req, res, next) => {
    req.requestTime = Date.now();
    next();
  });
};

module.exports = {
  applyCommonMiddleware
};
