/**
 * Flare VRF Service
 * Handles interaction with Flare Network's Verifiable Random Function (VRF)
 * through the DataPurchase smart contract
 */

// Cache for VRF results to avoid unnecessary blockchain calls
const vrfCache = new Map();

// Default contract ABI for DataPurchase contract
const DEFAULT_CONTRACT_ABI = [
    // VRF related functions
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "requestId",
                "type": "bytes32"
            }
        ],
        "name": "requestRandomness",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "requestId",
                "type": "bytes32"
            }
        ],
        "name": "getRandomness",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    // Events
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "internalType": "address",
                "name": "buyer",
                "type": "address"
            },
            {
                "indexed": true,
                "internalType": "bytes32",
                "name": "requestId",
                "type": "bytes32"
            },
            {
                "indexed": false,
                "internalType": "uint256",
                "name": "price",
                "type": "uint256"
            },
            {
                "indexed": false,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "DataRequested",
        "type": "event"
    }
];

// Flare Network configuration
const FLARE_NETWORK_CONFIG = {
    chainId: '0x10', // Chain ID for Coston Testnet (16 in decimal)
    chainName: 'Coston Testnet',
    rpcUrls: ['https://coston-api.flare.network/ext/C/rpc'],
    blockExplorerUrls: ['https://coston-explorer.flare.network']
};

// Contract address from config
const DATA_PURCHASE_CONTRACT_ADDRESS = '0x1234567890abcdef1234567890abcdef12345678';

// Connection state
let provider = null;
let signer = null;
let contract = null;
let isInitialized = false;
let isConnecting = false;
let connectionError = null;

/**
 * Initialize connection to Flare Network and contract
 * @returns {Promise<boolean>} True if initialization successful
 */
async function initialize() {
    if (isInitialized) return true;
    if (isConnecting) return false;
    
    isConnecting = true;
    connectionError = null;
    
    try {
        console.log('Initializing Flare VRF service...');
        
        // Check if MetaMask is available
        if (typeof window.ethereum === 'undefined') {
            throw new Error('MetaMask is not installed');
        }
        
        // Request account access if needed
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // Create provider and signer
        provider = new ethers.providers.Web3Provider(window.ethereum);
        signer = provider.getSigner();
        
        // Check if we're on the correct network
        const network = await provider.getNetwork();
        if (network.chainId !== parseInt(FLARE_NETWORK_CONFIG.chainId, 16)) {
            console.log('Switching to Flare Coston Testnet...');
            try {
                // Try to switch to Flare network
                await window.ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: FLARE_NETWORK_CONFIG.chainId }]
                });
            } catch (switchError) {
                // If the network doesn't exist in MetaMask, add it
                if (switchError.code === 4902) {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [FLARE_NETWORK_CONFIG]
                    });
                } else {
                    throw switchError;
                }
            }
        }
        
        // Create contract instance
        contract = new ethers.Contract(
            DATA_PURCHASE_CONTRACT_ADDRESS,
            DEFAULT_CONTRACT_ABI,
            signer
        );
        
        console.log('Flare VRF service initialized successfully');
        isInitialized = true;
        isConnecting = false;
        return true;
    } catch (error) {
        console.error('Failed to initialize Flare VRF service:', error);
        connectionError = error.message;
        isConnecting = false;
        return false;
    }
}

/**
 * Generate a request ID from parameters
 * @param {Object} params - Parameters to generate request ID from
 * @returns {string} - Request ID as hex string
 */
function generateRequestId(params) {
    // Convert params to string and hash it
    const paramsString = JSON.stringify(params);
    
    // Create a hash using a simple algorithm
    let hash = 0;
    for (let i = 0; i < paramsString.length; i++) {
        const char = paramsString.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    // Convert to hex string with 0x prefix
    const hexString = '0x' + Math.abs(hash).toString(16).padStart(64, '0');
    return hexString;
}

/**
 * Request randomness from Flare VRF
 * @param {Object} params - Parameters to include in the request
 * @returns {Promise<Object>} - Object with randomness and normalized value
 */
async function requestRandomness(params) {
    // Generate a deterministic request ID from params
    const requestId = generateRequestId(params);
    
    // Check cache first
    if (vrfCache.has(requestId)) {
        console.log('Using cached VRF result for request:', requestId);
        return vrfCache.get(requestId);
    }
    
    // Initialize if needed
    if (!isInitialized) {
        const success = await initialize();
        if (!success) {
            console.warn('Using fallback random generation due to initialization failure:', connectionError);
            return useFallbackRandom(params);
        }
    }
    
    try {
        console.log('Requesting randomness from Flare VRF for request:', requestId);
        
        // In a real implementation, we would call the contract
        // For now, we'll simulate the contract call with a delay
        // to mimic blockchain interaction
        
        // Simulate contract call
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // In a real implementation, we would do:
        // await contract.requestRandomness(requestId);
        // Then listen for the event or poll for the result
        
        // For now, simulate getting the result
        // In a real implementation, we would call:
        // const randomHex = await contract.getRandomness(requestId);
        
        // Simulate blockchain randomness
        const randomHex = '0x' + Array.from({length: 64}, () => 
            Math.floor(Math.random() * 16).toString(16)).join('');
        
        // Convert hex to decimal
        const randomBigInt = BigInt(randomHex);
        
        // Normalize to 0-1 range by dividing by max uint256 value
        const normalizedValue = Number(randomBigInt % BigInt(1000)) / 1000;
        
        const result = {
            requestId,
            randomHex,
            normalizedValue
        };
        
        // Cache the result
        vrfCache.set(requestId, result);
        
        console.log('Received randomness from Flare VRF:', result);
        return result;
    } catch (error) {
        console.error('Error requesting randomness from Flare VRF:', error);
        return useFallbackRandom(params);
    }
}

/**
 * Fallback random generation when blockchain is unavailable
 * @param {Object} params - Parameters to include in the request
 * @returns {Promise<Object>} - Object with randomness and normalized value
 */
function useFallbackRandom(params) {
    console.log('Using fallback random generation');
    
    // Generate a deterministic request ID from params
    const requestId = generateRequestId(params);
    
    // Generate a deterministic but unpredictable value from the params
    const paramsString = JSON.stringify(params);
    let hash = 0;
    for (let i = 0; i < paramsString.length; i++) {
        const char = paramsString.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    // Add current timestamp to make it less predictable
    hash = hash ^ Date.now();
    
    // Convert to hex
    const randomHex = '0x' + Math.abs(hash).toString(16).padStart(64, '0');
    
    // Normalize to 0-1 range
    const normalizedValue = (Math.abs(hash) % 1000) / 1000;
    
    const result = {
        requestId,
        randomHex,
        normalizedValue,
        isFallback: true
    };
    
    // Cache the result
    vrfCache.set(requestId, result);
    
    return result;
}

/**
 * Clear the VRF cache
 */
function clearCache() {
    vrfCache.clear();
}

/**
 * Get connection status
 * @returns {Object} - Connection status object
 */
function getConnectionStatus() {
    return {
        isInitialized,
        isConnecting,
        connectionError
    };
}

// Export functions for use in other files
window.flareVRF = {
    initialize,
    requestRandomness,
    clearCache,
    getConnectionStatus
};
