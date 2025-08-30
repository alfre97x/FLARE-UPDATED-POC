/**
 * Server configuration
 * Loads environment variables and provides configuration for the server
 */

// Load environment variables from .env file
require('dotenv').config();

// Configuration object
const config = {
  // Server configuration
  port: process.env.PORT || 3001,
  
  // Copernicus Data Space Ecosystem (CDSE) configuration
  cdse: {
    clientId: process.env.CDSE_CLIENT_ID,
    clientSecret: process.env.CDSE_CLIENT_SECRET,
    tokenUrl: process.env.CDSE_TOKEN_URL,
    apiUrl: process.env.CDSE_API_URL,
    zipperUrl: process.env.CDSE_ZIPPER_URL,
    stacUrl: process.env.CDSE_STAC_URL
  },
  
  // AI service configuration
  ai: {
    apiKey: process.env.AI_API_KEY,
    apiUrl: process.env.AI_API_URL
  },
  
  // Flare blockchain configuration
  flare: {
    networkUrl: process.env.RPC_URL,
    contractAddress: process.env.DATAPURCHASE_CONTRACT_ADDRESS,
    fdcHubAddress: process.env.FDC_HUB_ADDRESS,
    fdcVerificationAddress: process.env.FDC_VERIFICATION_ADDRESS,
    fdcRequestFeeConfigurationsAddress: process.env.FDC_REQUEST_FEE_CONFIGURATIONS_ADDRESS,
    fdcInflationConfigurationsAddress: process.env.FDC_INFLATION_CONFIGURATIONS_ADDRESS,
    daLayerApi: process.env.DA_LAYER_API,
    verifierApi: process.env.VERIFIER_API
  }
};

// Validate required configuration
const validateConfig = () => {
  const requiredCdseVars = ['clientId', 'clientSecret', 'tokenUrl', 'apiUrl'];
  
  for (const key of requiredCdseVars) {
    if (!config.cdse[key]) {
      console.warn(`Missing required CDSE configuration: ${key}`);
    }
  }
};

// Run validation
validateConfig();

module.exports = config;
