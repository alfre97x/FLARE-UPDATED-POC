
/**
 * Web-specific entry point for the Space Data Purchase application
 * This file ensures proper React initialization for the web environment
 */

import React from 'react';
import ReactDOM from 'react-dom';
import './space-data-app/config'; // Import config to ensure environment variables are set

// Import the App component
import App from './App';

// Ensure React is properly initialized for web
// This helps prevent the "Invalid hook call" error
if (typeof window !== 'undefined') {
  // Make React available globally to ensure consistent context
  window.React = React;
  window.ReactDOM = ReactDOM;
}

// Create a root element if it doesn't exist
const rootElement = document.getElementById('root') || document.createElement('div');
if (!rootElement.id) {
  rootElement.id = 'root';
  document.body.appendChild(rootElement);
}

// Use legacy render method instead of createRoot for better compatibility
ReactDOM.render(<App />, rootElement);
