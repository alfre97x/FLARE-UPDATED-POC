/**
 * Test script for AI service
 * Run with: node scripts/test_ai_service.js
 */

const axios = require('axios');
require('dotenv').config();

const OPENAI_API_KEY = process.env.AI_API_KEY;
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

console.log('AI Service Test');
console.log('==============');
console.log('');

// Check if API key is set
if (!OPENAI_API_KEY) {
  console.error('❌ AI_API_KEY is not set in .env file');
  console.log('');
  console.log('To fix this:');
  console.log('1. Create a .env file in the root directory (if not exists)');
  console.log('2. Add: AI_API_KEY=your_openai_api_key_here');
  console.log('3. Get your API key from: https://platform.openai.com/api-keys');
  process.exit(1);
} else {
  console.log('✅ AI_API_KEY is set');
  console.log(`   Key starts with: ${OPENAI_API_KEY.substring(0, 10)}...`);
}

// Test OpenAI API connection
async function testOpenAI() {
  console.log('');
  console.log('Testing OpenAI API connection...');
  
  try {
    const response = await axios.post(
      OPENAI_API_URL,
      {
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: 'You are a test assistant.' },
          { role: 'user', content: 'Say "OpenAI connection successful" and nothing else.' }
        ],
        max_tokens: 50,
        temperature: 0
      },
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('✅ OpenAI API connection successful');
    console.log(`   Response: ${response.data.choices[0].message.content}`);
    console.log(`   Model used: ${response.data.model}`);
    
    return true;
  } catch (error) {
    console.error('❌ OpenAI API connection failed');
    
    if (error.response) {
      console.log(`   Status: ${error.response.status}`);
      console.log(`   Error: ${error.response.data?.error?.message || error.response.statusText}`);
      
      if (error.response.status === 401) {
        console.log('');
        console.log('Authentication failed. Please check your API key.');
      } else if (error.response.status === 429) {
        console.log('');
        console.log('Rate limit exceeded or quota reached. Check your OpenAI account.');
      } else if (error.response.status === 404) {
        console.log('');
        console.log('Model not found. The gpt-4o-mini model might not be available.');
        console.log('Consider using gpt-3.5-turbo instead.');
      }
    } else {
      console.log(`   Error: ${error.message}`);
    }
    
    return false;
  }
}

// Test Vision API (for image analysis)
async function testVisionAPI() {
  console.log('');
  console.log('Testing OpenAI Vision API...');
  
  try {
    // Test with a simple base64 image (1x1 red pixel)
    const testImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';
    
    const response = await axios.post(
      OPENAI_API_URL,
      {
        model: 'gpt-4o', // Vision model
        messages: [
          { 
            role: 'user', 
            content: [
              { type: 'text', text: 'What color is this image? Just say the color.' },
              { type: 'image_url', image_url: { url: testImage, detail: 'low' } }
            ]
          }
        ],
        max_tokens: 50,
        temperature: 0
      },
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('✅ OpenAI Vision API works');
    console.log(`   Response: ${response.data.choices[0].message.content}`);
    
    return true;
  } catch (error) {
    console.error('❌ OpenAI Vision API failed');
    
    if (error.response) {
      console.log(`   Status: ${error.response.status}`);
      console.log(`   Error: ${error.response.data?.error?.message || error.response.statusText}`);
      
      if (error.response.status === 404) {
        console.log('');
        console.log('Vision model (gpt-4o) not available. You may need to upgrade your OpenAI account.');
        console.log('The app will fall back to text-based analysis.');
      }
    } else {
      console.log(`   Error: ${error.message}`);
    }
    
    return false;
  }
}

// Run tests
async function runTests() {
  const apiWorks = await testOpenAI();
  
  if (apiWorks) {
    await testVisionAPI();
  }
  
  console.log('');
  console.log('Test complete!');
  
  if (apiWorks) {
    console.log('');
    console.log('✅ Your AI service should be working properly.');
    console.log('If you still see default/mock data, restart your servers:');
    console.log('   npm run dev');
  } else {
    console.log('');
    console.log('⚠️  Please fix the issues above before using the AI features.');
  }
}

runTests();
