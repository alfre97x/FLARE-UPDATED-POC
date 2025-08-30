/**
 * Test script for DataPurchase contract
 * This script tests the basic functionality of the DataPurchase contract
 */

const { Web3 } = require('web3');
const fs = require('fs');
const path = require('path');

// Load environment variables with explicit path
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

// Verify RPC_URL is loaded
const rpcUrl = process.env.RPC_URL;
if (!rpcUrl) {
    console.error('ERROR: RPC_URL not found in environment variables');
    console.error('Make sure the .env file exists and contains RPC_URL');
    process.exit(1);
}
console.log(`Connecting to RPC URL: ${rpcUrl}`);

// Load contract ABIs with absolute paths
const dataPurchaseABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/datapurchase_abi.json'), 'utf8'));
const fdcVerificationABI = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../abi/fdc_verification_abi.json'), 'utf8'));

// Connect to Flare Coston2 testnet
const web3 = new Web3(process.env.RPC_URL);

// Set up account from private key
const privateKey = process.env.PRIVATE_KEY.startsWith('0x') ? process.env.PRIVATE_KEY : `0x${process.env.PRIVATE_KEY}`;
const account = web3.eth.accounts.privateKeyToAccount(privateKey);
web3.eth.accounts.wallet.add(account);
const fromAddress = account.address;

// Contract addresses from .env
const dataPurchaseAddress = process.env.DATAPURCHASE_CONTRACT_ADDRESS;
const fdcVerificationAddress = process.env.FDC_VERIFICATION_ADDRESS;

// Create contract instances
const dataPurchaseContract = new web3.eth.Contract(dataPurchaseABI, dataPurchaseAddress);
const fdcVerificationContract = new web3.eth.Contract(fdcVerificationABI, fdcVerificationAddress);

// Test functions
async function testContractDeployment() {
    console.log('\n--- Testing Contract Deployment ---');
    
    try {
        // Check if the contract exists by calling a view function
        const owner = await dataPurchaseContract.methods.owner().call();
        console.log(`✅ Contract deployed at ${dataPurchaseAddress}`);
        console.log(`✅ Contract owner: ${owner}`);
        
        // Check if the FDC verifier is set correctly
        const fdcVerifier = await dataPurchaseContract.methods.fdcVerifier().call();
        console.log(`✅ FDC Verifier set to: ${fdcVerifier}`);
        console.log(`✅ Expected FDC Verifier: ${fdcVerificationAddress}`);
        
        if (fdcVerifier.toLowerCase() !== fdcVerificationAddress.toLowerCase()) {
            console.warn('⚠️ FDC Verifier address does not match the one in .env file');
        }
        
        return true;
    } catch (error) {
        console.error('❌ Contract deployment test failed:', error.message);
        return false;
    }
}

async function testPurchaseFunction() {
    console.log('\n--- Testing Purchase Function ---');
    
    try {
        // Generate a test request ID
        const requestId = web3.utils.keccak256('test-request-' + Date.now());
        console.log(`📝 Test Request ID: ${requestId}`);
        
        // Check account balance
        const balance = await web3.eth.getBalance(fromAddress);
        console.log(`💰 Account balance: ${web3.utils.fromWei(balance, 'ether')} FLR`);
        
        // Set up purchase transaction
        const paymentAmount = web3.utils.toWei('0.01', 'ether'); // 0.01 FLR
        console.log(`💸 Payment amount: ${web3.utils.fromWei(paymentAmount, 'ether')} FLR`);
        
        // Estimate gas for the transaction
        const gasEstimate = await dataPurchaseContract.methods.purchase(requestId).estimateGas({
            from: fromAddress,
            value: paymentAmount
        });
        console.log(`⛽ Estimated gas: ${gasEstimate}`);
        
        // Calculate gas with buffer (20%)
        const gasWithBuffer = Math.floor(Number(gasEstimate) * 1.2).toString();
        console.log(`⛽ Gas with buffer: ${gasWithBuffer}`);
        
        // Send purchase transaction
        console.log('🔄 Sending purchase transaction...');
        const receipt = await dataPurchaseContract.methods.purchase(requestId).send({
            from: fromAddress,
            value: paymentAmount,
            gas: gasWithBuffer
        });
        
        console.log(`✅ Transaction successful! Hash: ${receipt.transactionHash}`);
        
        // Check for DataRequested event
        const events = receipt.events;
        if (events && events.DataRequested) {
            console.log('✅ DataRequested event emitted');
            console.log(`✅ Event buyer: ${events.DataRequested.returnValues.buyer}`);
            console.log(`✅ Event requestId: ${events.DataRequested.returnValues.requestId}`);
        } else {
            console.warn('⚠️ DataRequested event not found in transaction receipt');
        }
        
        // Check if request was stored in contract
        const request = await dataPurchaseContract.methods.requests(requestId).call();
        console.log(`✅ Request stored in contract: buyer=${request.buyer}, delivered=${request.delivered}`);
        
        return {
            success: true,
            requestId: requestId
        };
    } catch (error) {
        console.error('❌ Purchase function test failed:', error.message);
        return {
            success: false,
            error: error.message
        };
    }
}

async function testDeliverDataFunction(requestId) {
    console.log('\n--- Testing DeliverData Function ---');
    
    if (!requestId) {
        console.error('❌ No requestId provided for testing deliverData');
        return false;
    }
    
    console.log(`📝 Using Request ID: ${requestId}`);
    
    try {
        // In a real scenario, we would get these from the FDC system
        // For testing, we'll use mock values
        const attestationResponse = web3.utils.keccak256('mock-attestation-' + Date.now());
        const mockProof = web3.utils.hexToBytes('0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef');
        
        console.log(`📝 Mock Attestation Response: ${attestationResponse}`);
        console.log(`📝 Mock Proof Length: ${mockProof.length} bytes`);
        
        // Note: This will likely fail in a real test because the mock proof won't be valid
        // We would need a real attestation and proof from the FDC system
        console.log('⚠️ This test will likely fail because we are using mock data');
        console.log('⚠️ In a real scenario, we would need a valid attestation and proof from the FDC system');
        
        // Try to deliver data
        console.log('🔄 Attempting to deliver data...');
        
        try {
            // Estimate gas for the transaction
            const gasEstimate = await dataPurchaseContract.methods.deliverData(
                requestId,
                attestationResponse,
                mockProof
            ).estimateGas({
                from: fromAddress
            });
            console.log(`⛽ Estimated gas: ${gasEstimate}`);
            
            // Calculate gas with buffer (20%)
            const gasWithBuffer = Math.floor(Number(gasEstimate) * 1.2).toString();
            console.log(`⛽ Gas with buffer: ${gasWithBuffer}`);
            
            // Send deliverData transaction
            const receipt = await dataPurchaseContract.methods.deliverData(
                requestId,
                attestationResponse,
                mockProof
            ).send({
                from: fromAddress,
                gas: gasWithBuffer
            });
            
            console.log(`✅ Transaction successful! Hash: ${receipt.transactionHash}`);
            
            // Check for DataDelivered event
            const events = receipt.events;
            if (events && events.DataDelivered) {
                console.log('✅ DataDelivered event emitted');
                console.log(`✅ Event requestId: ${events.DataDelivered.returnValues.requestId}`);
                console.log(`✅ Event dataHash: ${events.DataDelivered.returnValues.dataHash}`);
            } else {
                console.warn('⚠️ DataDelivered event not found in transaction receipt');
            }
            
            // Check if request was marked as delivered
            const request = await dataPurchaseContract.methods.requests(requestId).call();
            console.log(`✅ Request updated in contract: buyer=${request.buyer}, delivered=${request.delivered}`);
            
            return true;
        } catch (error) {
            console.error('❌ DeliverData transaction failed:', error.message);
            console.log('ℹ️ This is expected if using mock data. In a real scenario, we would need valid attestation and proof.');
            
            // Check if we can verify the attestation directly
            try {
                console.log('🔄 Trying to verify attestation directly...');
                const isValid = await fdcVerificationContract.methods.verifyAttestation(
                    requestId,
                    attestationResponse,
                    mockProof
                ).call();
                console.log(`ℹ️ Direct verification result: ${isValid}`);
            } catch (verifyError) {
                console.error('❌ Direct verification failed:', verifyError.message);
            }
            
            return false;
        }
    } catch (error) {
        console.error('❌ DeliverData function test failed:', error.message);
        return false;
    }
}

// Main test function
async function runTests() {
    console.log('=== DataPurchase Contract Test ===');
    console.log(`🔗 Connected to: ${process.env.RPC_URL}`);
    console.log(`📝 Testing contract at: ${dataPurchaseAddress}`);
    console.log(`👤 Using account: ${fromAddress}`);
    
    // Test contract deployment
    const deploymentOk = await testContractDeployment();
    if (!deploymentOk) {
        console.error('❌ Deployment test failed. Stopping tests.');
        return;
    }
    
    // Test purchase function
    const purchaseResult = await testPurchaseFunction();
    if (!purchaseResult.success) {
        console.error('❌ Purchase test failed. Stopping tests.');
        return;
    }
    
    // Test deliverData function
    await testDeliverDataFunction(purchaseResult.requestId);
    
    console.log('\n=== Test Complete ===');
}

// Run the tests
runTests()
    .then(() => process.exit(0))
    .catch(error => {
        console.error('Unhandled error during tests:', error);
        process.exit(1);
    });
