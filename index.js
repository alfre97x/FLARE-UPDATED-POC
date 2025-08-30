/**
 * Main entry point for the Space Data Purchase application
 * This file handles initialization for both web and native platforms
 */

import { registerRootComponent } from 'expo';
import { Platform } from 'react-native';
import App from './App';

// Log the platform we're running on
if (Platform.OS === 'web') {
  console.log('Running in web environment');
  // For web, we use web.js as the entry point
  // This prevents duplicate React contexts
} else {
  console.log(`Running in ${Platform.OS} environment`);
  // Only register the root component for non-web platforms
  registerRootComponent(App);
}
