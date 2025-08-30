/**
 * Flare Services - Blockchain integration for SpaceData application
 * Provides functions for interacting with the Flare blockchain
 */

const API_BASE = (window.RUNTIME_CONFIG && window.RUNTIME_CONFIG.NODE_API_BASE) || '';

// Global variables
let web3;
let dataPurchaseContract;
let fdcHubContract;
let fdcVerificationContract;
let currentAccount;
let isInitialized = false;

 // Contract addresses and ABIs
let contractConfig = {
    rpcUrl: 'https://coston2-api.flare.network/ext/C/rpc',
    dataPurchaseAddress: '',
    fdcHubAddress: '',
    fdcVerificationAddress: '',
    daLayerApi: 'https://api.da.coston2.flare.network'
};

 // Fallback address (same one used in other web modules) in case backend config is missing
const FALLBACK_DATA_PURCHASE_ADDRESS = '0x2330d0cc23fd6764b7c67023c8fb85ae7287bfc9';

// Network configuration (populated from backend)
let networkConfig = {
    chainId: '0x72',
    chainName: 'Coston2 Testnet',
    rpcUrls: ['https://coston2-api.flare.network/ext/C/rpc'],
    blockExplorerUrls: ['https://coston2-explorer.flare.network'],
    nativeCurrency: { name: 'Coston2 Flare', symbol: 'C2FLR', decimals: 18 }
};

 // Ensure MetaMask is connected to the target network from backend config
async function ensureTargetNetwork(target) {
    if (!window.ethereum || !target || !target.chainId) return;
    try {
        const desired = (target.chainId || '').toLowerCase();
        const current = ((await window.ethereum.request({ method: 'eth_chainId' })) || '').toLowerCase();
        if (current !== desired) {
            try {
                await window.ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: desired }]
                });
            } catch (e) {
                if (e.code === 4902) {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: desired,
                            chainName: target.chainName || 'Flare Testnet',
                            rpcUrls: target.rpcUrls && target.rpcUrls.length ? target.rpcUrls : [contractConfig.rpcUrl],
                            nativeCurrency: target.nativeCurrency || { name: 'FLR', symbol: 'FLR', decimals: 18 },
                            blockExplorerUrls: target.blockExplorerUrls || []
                        }]
                    });
                } else if (e.code === 4001) {
                    // user rejected
                    throw e;
                } else {
                    console.warn('wallet_switchEthereumChain failed, attempting wallet_addEthereumChain with provided params:', e);
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: desired,
                            chainName: target.chainName || 'Flare Testnet',
                            rpcUrls: target.rpcUrls && target.rpcUrls.length ? target.rpcUrls : [contractConfig.rpcUrl],
                            nativeCurrency: target.nativeCurrency || { name: 'FLR', symbol: 'FLR', decimals: 18 },
                            blockExplorerUrls: target.blockExplorerUrls || []
                        }]
                    });
                }
            }
        }
    } catch (err) {
        console.warn('ensureTargetNetwork: unable to switch network:', err);
    }
}

/**
 * Initialize blockchain connection and contracts
 * @returns {Promise<boolean>} True if initialization was successful
 */
async function initializeBlockchain() {
    try {
        // Check if Web3 is already injected by MetaMask
        if (window.ethereum) {
            web3 = new Web3(window.ethereum);
            
            try {
                // Request account access
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                currentAccount = accounts[0];
                console.log('Connected account:', currentAccount);
                
                // Set up event listeners for account changes
                window.ethereum.on('accountsChanged', (accounts) => {
                    currentAccount = accounts[0];
                    console.log('Account changed to:', currentAccount);
                });
                
                // Fetch contract configuration from backend
                const response = await fetch(`${API_BASE}/api/blockchain/config`);
                const config = await response.json();
                
                // Update contract configuration
                contractConfig = {
                    rpcUrl: config.rpcUrl || contractConfig.rpcUrl,
                    dataPurchaseAddress: config.dataPurchaseContractAddress || contractConfig.dataPurchaseAddress,
                    fdcHubAddress: config.fdcHubAddress || contractConfig.fdcHubAddress,
                    fdcVerificationAddress: config.fdcVerificationAddress || contractConfig.fdcVerificationAddress,
                    daLayerApi: config.daLayerApi || contractConfig.daLayerApi
                };
                
                if (!contractConfig.dataPurchaseAddress) {
                    console.warn('DataPurchase contract address is missing from backend config.');
                    if (typeof FALLBACK_DATA_PURCHASE_ADDRESS === 'string' && FALLBACK_DATA_PURCHASE_ADDRESS) {
                        contractConfig.dataPurchaseAddress = FALLBACK_DATA_PURCHASE_ADDRESS;
                        console.info('Using fallback DataPurchase address:', contractConfig.dataPurchaseAddress);
                    } else {
                        alert('Payment contract address is not configured. Please set DATAPURCHASE_CONTRACT_ADDRESS on the server.');
                    }
                }
                console.log('Final contract configuration:', contractConfig);

                // Build and ensure target network from backend config (supports Coston3)
                networkConfig = {
                    chainId: (config.chainId || '0x72').toLowerCase(),
                    chainName: config.chainName || 'Flare Testnet',
                    rpcUrls: config.rpcUrl ? [config.rpcUrl] : ['https://coston2-api.flare.network/ext/C/rpc'],
                    blockExplorerUrls: (config.blockExplorerUrls && config.blockExplorerUrls.length) ? config.blockExplorerUrls : [],
                    nativeCurrency: config.nativeCurrency || { name: 'FLR', symbol: 'FLR', decimals: 18 }
                };
                await ensureTargetNetwork(networkConfig);
                const connectedChainId = await window.ethereum.request({ method: 'eth_chainId' });
                console.log('Connected chainId:', connectedChainId);
                
                // Initialize contracts
                await initializeContracts();
                
                isInitialized = true;
                return true;
            } catch (error) {
                console.error('User denied account access or error occurred:', error);
                return false;
            }
        } else {
            console.error('MetaMask not detected');
            return false;
        }
    } catch (error) {
        console.error('Error initializing blockchain:', error);
        return false;
    }
}

/**
 * Initialize contract instances
 * @returns {Promise<void>}
 */
async function initializeContracts() {
    try {
        // Load ABIs
        const dataPurchaseAbi = await fetch(`${API_BASE}/abi/datapurchase_abi.json`).then(res => res.json());
        const fdcHubAbi = await fetch(`${API_BASE}/abi/fdc_hub_abi.json`).then(res => res.json());
        const fdcVerificationAbi = await fetch(`${API_BASE}/abi/fdc_verification_abi.json`).then(res => res.json());
        
        // Initialize contracts
        if (contractConfig.dataPurchaseAddress) {
            dataPurchaseContract = new web3.eth.Contract(dataPurchaseAbi, contractConfig.dataPurchaseAddress);
            console.log('DataPurchase contract initialized');
        }
        
        if (contractConfig.fdcHubAddress) {
            fdcHubContract = new web3.eth.Contract(fdcHubAbi, contractConfig.fdcHubAddress);
            console.log('FDC Hub contract initialized');
        }
        
        if (contractConfig.fdcVerificationAddress) {
            fdcVerificationContract = new web3.eth.Contract(fdcVerificationAbi, contractConfig.fdcVerificationAddress);
            console.log('FDC Verification contract initialized');
        }
    } catch (error) {
        console.error('Error initializing contracts:', error);
        throw error;
    }
}

/**
 * Check if blockchain is initialized
 * @returns {boolean} True if blockchain is initialized
 */
function isBlockchainInitialized() {
    return isInitialized;
}

/**
 * Get current account
 * @returns {string} Current account address
 */
function getCurrentAccount() {
    return currentAccount;
}

/**
 * Purchase data using the DataPurchase contract
 * @param {string} requestId Request ID
 * @param {number} amount Amount to pay in ETH
 * @returns {Promise<object>} Transaction receipt
 */
async function purchaseData(requestId, amount) {
    try {
        if (!isInitialized) {
            throw new Error('Blockchain not initialized');
        }
        
        if (!dataPurchaseContract) {
            throw new Error('DataPurchase contract not initialized');
        }
        
        // Ensure correct network before sending
        await ensureTargetNetwork(networkConfig);

        // Validate amount is a positive number
        const numericAmount = Number(amount);
        if (!isFinite(numericAmount) || numericAmount <= 0) {
            throw new Error('Invalid amount to pay. Computed amount was: ' + amount);
        }

        // Convert amount to wei
        const amountWei = web3.utils.toWei(numericAmount.toString(), 'ether');
        
        // Convert requestId to bytes32 if it's not already
        const requestIdBytes32 = web3.utils.isHexStrict(requestId) && requestId.length === 66
            ? requestId
            : web3.utils.keccak256(requestId);
        
        // Send transaction
        const receipt = await dataPurchaseContract.methods.purchase(requestIdBytes32)
            .send({
                from: currentAccount,
                value: amountWei,
                gas: 200000
            });
        
        console.log('Purchase transaction receipt:', receipt);
        return receipt;
    } catch (error) {
        console.error('Error purchasing data:', error);
        throw error;
    }
}

/**
 * Request attestation from FDC Hub
 * @param {string} attestationType Type of attestation
 * @param {string} parameters Parameters for attestation
 * @returns {Promise<object>} Transaction receipt
 */
async function requestAttestation(attestationType, parameters) {
    try {
        // Use backend API to request attestation
        const response = await fetch(`${API_BASE}/api/blockchain/request-attestation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                attestation_type: attestationType,
                parameters: parameters
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to request attestation');
        }
        
        console.log('Attestation requested:', result);
        return result;
    } catch (error) {
        console.error('Error requesting attestation:', error);
        throw error;
    }
}

/**
 * Fetch attestation result from DA Layer API
 * @param {string} requestId Request ID
 * @returns {Promise<object>} Attestation result
 */
async function fetchAttestationResult(requestId) {
    try {
        // Use backend API to fetch attestation result
        const response = await fetch(`${API_BASE}/api/blockchain/fetch-attestation/${requestId}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to fetch attestation result');
        }
        
        console.log('Attestation result:', result);
        return result;
    } catch (error) {
        console.error('Error fetching attestation result:', error);
        throw error;
    }
}

/**
 * Verify attestation using FDC Verification contract
 * @param {string} requestId Request ID
 * @param {string} attestationResponse Attestation response
 * @param {string} proof Proof
 * @returns {Promise<boolean>} True if attestation is valid
 */
async function verifyAttestation(requestId, attestationResponse, proof) {
    try {
        // Use backend API to verify attestation
        const response = await fetch(`${API_BASE}/api/blockchain/verify-attestation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: requestId,
                attestation_response: attestationResponse,
                proof: proof
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to verify attestation');
        }
        
        console.log('Attestation verification result:', result);
        return result.verified;
    } catch (error) {
        console.error('Error verifying attestation:', error);
        throw error;
    }
}

/**
 * Deliver data to DataPurchase contract
 * @param {string} requestId Request ID
 * @param {string} attestationResponse Attestation response
 * @param {string} proof Proof
 * @returns {Promise<object>} Transaction receipt
 */
async function deliverData(requestId, attestationResponse, proof) {
    try {
        // Use backend API to deliver data
        const response = await fetch(`${API_BASE}/api/blockchain/deliver-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request_id: requestId,
                attestation_response: attestationResponse,
                proof: proof
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to deliver data');
        }
        
        console.log('Data delivered:', result);
        return result;
    } catch (error) {
        console.error('Error delivering data:', error);
        throw error;
    }
}

/**
 * Generate a request ID for a data request
 * @param {object} dataInfo Dictionary with data information
 * @returns {Promise<string>} Request ID
 */
async function generateRequestId(dataInfo) {
    try {
        // Use backend API to generate request ID
        const response = await fetch(`${API_BASE}/api/blockchain/generate-request-id`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_info: dataInfo
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to generate request ID');
        }
        
        console.log('Generated request ID:', result.requestId);
        return result.requestId;
    } catch (error) {
        console.error('Error generating request ID:', error);
        throw error;
    }
}

/**
 * Listen for DataRequested events
 * @param {function} callback Callback function to handle events
 * @returns {object} Subscription object
 */
function listenForDataRequested(callback) {
    if (!isInitialized || !dataPurchaseContract) {
        throw new Error('Blockchain not initialized');
    }
    
    return dataPurchaseContract.events.DataRequested()
        .on('data', (event) => {
            console.log('DataRequested event:', event);
            callback(event);
        })
        .on('error', (error) => {
            console.error('Error in DataRequested event:', error);
        });
}

/**
 * Listen for DataDelivered events
 * @param {function} callback Callback function to handle events
 * @returns {object} Subscription object
 */
function listenForDataDelivered(callback) {
    if (!isInitialized || !dataPurchaseContract) {
        throw new Error('Blockchain not initialized');
    }
    
    return dataPurchaseContract.events.DataDelivered()
        .on('data', (event) => {
            console.log('DataDelivered event:', event);
            callback(event);
        })
        .on('error', (error) => {
            console.error('Error in DataDelivered event:', error);
        });
}

// Export functions
window.FlareServices = {
    initializeBlockchain,
    isBlockchainInitialized,
    getCurrentAccount,
    purchaseData,
    requestAttestation,
    fetchAttestationResult,
    verifyAttestation,
    deliverData,
    generateRequestId,
    listenForDataRequested,
    listenForDataDelivered
};
