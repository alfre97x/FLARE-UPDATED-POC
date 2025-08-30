const express = require('express');
const path = require('path');
const app = express();
const config = require('./server/config');

// Import middleware
const { applyCommonMiddleware } = require('./server/middleware/common');
const { notFound, errorHandler } = require('./server/middleware/error');

// Import routes
const copernicusRoutes = require('./server/routes/copernicus');
const blockchainRoutes = require('./server/routes/blockchain');
const aiRoutes = require('./server/routes/ai');

// Apply common middleware (CORS, body parser, logging)
applyCommonMiddleware(app);

// Serve static files from the web-app directory
app.use('/web-app', express.static(path.join(__dirname, 'web-app')));
app.use(express.static(path.join(__dirname, 'web-app')));

// Serve ABI files from the abi directory
app.use('/abi', express.static(path.join(__dirname, 'abi')));

// Serve assets from space-data-app/assets directory
app.use('/assets', express.static(path.join(__dirname, 'space-data-app', 'assets')));

// API routes
app.use('/api/copernicus', copernicusRoutes);
app.use('/api/blockchain', blockchainRoutes);
app.use('/api/ai', aiRoutes);

// Serve the index.html file for the root path
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'web-app', 'index.html'));
});

// Serve the HTML files directly for specific paths
app.get('/web-app/data-selection.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'web-app', 'data-selection.html'));
});

app.get('/web-app/data-results.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'web-app', 'data-results.html'));
});

// Serve the index.html file for any other path (for client-side routing)
app.use((req, res, next) => {
  // Only serve index.html for non-API routes and GET requests that don't have a file extension
  if (req.method === 'GET' && !req.path.startsWith('/api/') && !req.path.includes('.')) {
    res.sendFile(path.join(__dirname, 'web-app', 'index.html'));
  } else {
    next();
  }
});

// Error handling middleware
app.use(notFound);
app.use(errorHandler);

/**
 * Bind to provided PORT/0.0.0.0 in cloud (e.g., Railway), default 3001 locally
 * This ensures the service responds behind the platform's proxy/router.
 */
const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3001;
const host = process.env.HOST || '0.0.0.0';

// Start the server
app.listen(port, host, () => {
  const displayHost = host === '0.0.0.0' ? 'localhost' : host;
  console.log(`Server running at http://${displayHost}:${port}`);
  console.log(`Access the application at http://${displayHost}:${port}/web-app`);
  console.log(`API available at http://${displayHost}:${port}/api`);
});
