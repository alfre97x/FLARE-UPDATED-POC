/**
 * Test script for blockchain API endpoints
 * 
 * This script tests the blockchain API endpoints we've implemented:
 * - /api/blockchain/config
 * - /api/blockchain/verify
 * - /api/blockchain/purchase
 */

const fetch = require('node-fetch');

// Base URL for API requests
const API_BASE_URL = 'http://localhost:3001/api';

/**
 * Test the blockchain config endpoint
 */
async function testBlockchainConfig() {
  console.log('\n=== Testing /api/blockchain/config ===');
  
  try {
    const response = await fetch(`${API_BASE_URL}/blockchain/config`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Config data:', data);
    
    // Verify that the response contains the expected fields
    const requiredFields = [
      'dataPurchaseContractAddress',
      'fdcHubAddress',
      'fdcVerificationAddress',
      'rpcUrl',
      'daLayerApi'
    ];
    
    const missingFields = requiredFields.filter(field => !data[field]);
    
    if (missingFields.length > 0) {
      console.error('Missing required fields:', missingFields);
    } else {
      console.log('✅ All required fields are present');
    }
    
    return data;
  } catch (error) {
    console.error('Error testing blockchain config:', error);
    return null;
  }
}

/**
 * Test the blockchain verify endpoint
 */
async function testBlockchainVerify() {
  console.log('\n=== Testing /api/blockchain/verify ===');
  
  try {
    // Generate a mock request ID
    const requestId = `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`;
    
    const response = await fetch(`${API_BASE_URL}/blockchain/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ requestId })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Verification result:', data);
    
    // Verify that the response contains the expected fields
    const requiredFields = [
      'verified',
      'status',
      'message',
      'attestationResponse',
      'proof'
    ];
    
    const missingFields = requiredFields.filter(field => !data[field] && data[field] !== false);
    
    if (missingFields.length > 0) {
      console.error('Missing required fields:', missingFields);
    } else {
      console.log('✅ All required fields are present');
    }
    
    return data;
  } catch (error) {
    console.error('Error testing blockchain verify:', error);
    return null;
  }
}

/**
 * Test the blockchain purchase endpoint
 */
async function testBlockchainPurchase() {
  console.log('\n=== Testing /api/blockchain/purchase ===');
  
  try {
    // Create mock purchase data
    const purchaseData = {
      dataType: 'satellite.observation',
      coordinates: {
        type: 'Polygon',
        coordinates: [
          [
            [12.5, 41.9],
            [12.6, 41.9],
            [12.6, 42.0],
            [12.5, 42.0],
            [12.5, 41.9]
          ]
        ]
      },
      startDate: '2023-04-01',
      endDate: '2023-04-30',
      price: 0.01
    };
    
    const response = await fetch(`${API_BASE_URL}/blockchain/purchase`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(purchaseData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Purchase result:', data);
    
    // Verify that the response contains the expected fields
    const requiredFields = [
      'success',
      'requestId',
      'transactionHash',
      'attestationTransactionHash',
      'message'
    ];
    
    const missingFields = requiredFields.filter(field => !data[field] && data[field] !== false);
    
    if (missingFields.length > 0) {
      console.error('Missing required fields:', missingFields);
    } else {
      console.log('✅ All required fields are present');
    }
    
    return data;
  } catch (error) {
    console.error('Error testing blockchain purchase:', error);
    return null;
  }
}

/**
 * Run all tests
 */
async function runTests() {
  console.log('Starting blockchain API tests...');
  
  // Test blockchain config
  const configData = await testBlockchainConfig();
  
  // Test blockchain verify
  const verifyData = await testBlockchainVerify();
  
  // Test blockchain purchase
  const purchaseData = await testBlockchainPurchase();
  
  console.log('\n=== Test Summary ===');
  console.log('Config test:', configData ? '✅ Passed' : '❌ Failed');
  console.log('Verify test:', verifyData ? '✅ Passed' : '❌ Failed');
  console.log('Purchase test:', purchaseData ? '✅ Passed' : '❌ Failed');
}

// Run the tests
runTests();
