/**
 * Wallet connection functionality for SpaceData web application
 * Uses MetaMaskConnectionManager for reliable wallet interactions
 */

// Logging levels
const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

// Current log level - change to adjust verbosity
const CURRENT_LOG_LEVEL = LOG_LEVELS.DEBUG;

/**
 * Enhanced logging function with levels
 * @param {string} message - Message to log
 * @param {number} level - Log level (from LOG_LEVELS)
 * @param {any} data - Optional data to log
 */
function walletLog(message, level = LOG_LEVELS.INFO, data = null) {
    if (level >= CURRENT_LOG_LEVEL) {
        const timestamp = new Date().toISOString();
        const prefix = `[WALLET ${timestamp}]`;
        
        switch (level) {
            case LOG_LEVELS.DEBUG:
                console.debug(`${prefix} ${message}`, data || '');
                break;
            case LOG_LEVELS.INFO:
                console.log(`${prefix} ${message}`, data || '');
                break;
            case LOG_LEVELS.WARN:
                console.warn(`${prefix} ${message}`, data || '');
                break;
            case LOG_LEVELS.ERROR:
                console.error(`${prefix} ${message}`, data || '');
                break;
        }
    }
}

// Contract address from config
const FLARE_CONTRACT_ADDRESS = '0x2330d0cc23fd6764b7c67023c8fb85ae7287bfc9';

// Global variables to track connection state
let connectionErrors = [];

/**
 * Connect to MetaMask wallet using the MetaMask Connection Manager
 * @returns {Promise<boolean>} True if connection successful
 */
async function connectWallet() {
    walletLog("Attempting to connect wallet...", LOG_LEVELS.INFO);
    
    // Clear previous connection errors
    connectionErrors = [];
    
    try {
        // Check if MetaMask Connection Manager is available
        if (!window.metamaskManager) {
            walletLog("MetaMask Connection Manager not found, loading it now", LOG_LEVELS.WARN);
            
            // Create a script element to load the MetaMask Connection Manager
            const script = document.createElement('script');
            script.src = '/web-app/metamask-connection.js';
            script.async = true;
            
            // Wait for the script to load
            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
            
            // Check again if the manager is available
            if (!window.metamaskManager) {
                walletLog("Failed to load MetaMask Connection Manager", LOG_LEVELS.ERROR);
                
                connectionErrors.push({
                    time: new Date().toISOString(),
                    type: 'MANAGER_NOT_FOUND',
                    message: 'MetaMask Connection Manager not found'
                });
                
                // Fallback for development/testing
                if (confirm('MetaMask Connection Manager not found. Would you like to continue in development mode?\n\nIn development mode, you can test the application without a real wallet connection.')) {
                    // Simulate a successful connection with a mock account
                    walletLog("Connected to mock account in development mode", LOG_LEVELS.INFO);
                    
                    // Update UI to show connected state
                    updateConnectionUI('0x742d35Cc6634C0532925a3b844Bc454e4438f44e');
                    
                    return true;
                }
                
                return false;
            }
        }
        
        // Check if MetaMask is installed
        if (!window.metamaskManager.state.isMetaMaskInstalled) {
            walletLog("MetaMask not detected", LOG_LEVELS.WARN);
            
            connectionErrors.push({
                time: new Date().toISOString(),
                type: 'METAMASK_NOT_FOUND',
                message: 'MetaMask extension not detected in browser'
            });
            
            // Fallback for development/testing
            if (confirm('MetaMask not detected. Would you like to continue in development mode?\n\nIn development mode, you can test the application without a real wallet connection.')) {
                // Simulate a successful connection with a mock account
                walletLog("Connected to mock account in development mode", LOG_LEVELS.INFO);
                
                // Update UI to show connected state
                updateConnectionUI('0x742d35Cc6634C0532925a3b844Bc454e4438f44e');
                
                return true;
            } else {
                // User declined development mode, offer to install MetaMask
                if (confirm('Would you like to install MetaMask?')) {
                    window.open('https://metamask.io/download.html', '_blank');
                }
                return false;
            }
        }
        
        // Connect to MetaMask
        walletLog("Connecting to MetaMask using Connection Manager", LOG_LEVELS.INFO);
        
        // Set up event listeners for connection state changes
        window.metamaskManager.on('onConnectionStateChanged', handleConnectionStateChanged);
        window.metamaskManager.on('onNetworkStateChanged', handleNetworkStateChanged);
        window.metamaskManager.on('onAccountChanged', handleAccountChanged);
        window.metamaskManager.on('onError', handleConnectionError);
        
        // Connect to MetaMask
        const connected = await window.metamaskManager.connect();
        
        if (connected) {
            walletLog("Successfully connected to MetaMask", LOG_LEVELS.INFO, {
                account: window.metamaskManager.state.account,
                chainId: window.metamaskManager.state.chainId,
                balance: window.metamaskManager.state.balance
            });
            
            // Update UI to show connected state
            updateConnectionUI(window.metamaskManager.state.account);
            
            return true;
        } else {
            walletLog("Failed to connect to MetaMask", LOG_LEVELS.ERROR, {
                error: window.metamaskManager.state.error
            });
            
            connectionErrors.push({
                time: new Date().toISOString(),
                type: 'CONNECTION_FAILED',
                message: window.metamaskManager.state.error || 'Failed to connect to MetaMask'
            });
            
            alert('Failed to connect to MetaMask: ' + (window.metamaskManager.state.error || 'Unknown error'));
            
            return false;
        }
    } catch (error) {
        walletLog('Unexpected error connecting wallet', LOG_LEVELS.ERROR, error);
        
        connectionErrors.push({
            time: new Date().toISOString(),
            type: 'UNEXPECTED_ERROR',
            message: error.message,
            error
        });
        
        alert('Failed to connect wallet: ' + error.message);
        return false;
    }
}

/**
 * Handle connection state changes
 * @param {Object} state - New connection state
 */
function handleConnectionStateChanged(state) {
    walletLog("Connection state changed", LOG_LEVELS.INFO, state);
    
    if (state.connectionState === 'CONNECTED') {
        // Update UI to show connected state
        updateConnectionUI(state.account);
    } else if (state.connectionState === 'DISCONNECTED' || state.connectionState === 'ERROR') {
        // Update UI to show disconnected state
        updateConnectionUI(null);
        
        if (state.error) {
            walletLog("Connection error", LOG_LEVELS.ERROR, state.error);
            
            connectionErrors.push({
                time: new Date().toISOString(),
                type: 'CONNECTION_ERROR',
                message: state.error
            });
        }
    }
}

/**
 * Handle network state changes
 * @param {string} networkState - New network state
 */
function handleNetworkStateChanged(networkState) {
    walletLog("Network state changed", LOG_LEVELS.INFO, networkState);
    
    if (networkState === 'WRONG_NETWORK') {
        walletLog("Connected to wrong network", LOG_LEVELS.WARN);
        
        // Show warning to user
        alert("Warning: You are not connected to the Flare Coston2 Testnet. Some features may not work correctly.");
    }
}

/**
 * Handle account changes
 * @param {string} account - New account address
 */
function handleAccountChanged(account) {
    walletLog("Account changed", LOG_LEVELS.INFO, account);
    
    // Update UI to show new account
    updateConnectionUI(account);
}

/**
 * Handle connection errors
 * @param {Object} error - Error object
 */
function handleConnectionError(error) {
    walletLog("Connection error", LOG_LEVELS.ERROR, error);
    
    connectionErrors.push({
        time: new Date().toISOString(),
        type: 'CONNECTION_ERROR',
        message: error.message || 'Unknown error',
        error
    });
}

/**
 * Disconnect wallet
 */
function disconnectWallet() {
    walletLog("Disconnecting wallet", LOG_LEVELS.INFO);
    
    if (window.metamaskManager) {
        // Disconnect using the MetaMask Connection Manager
        window.metamaskManager.disconnect();
        
        walletLog("Wallet disconnected", LOG_LEVELS.INFO);
    }
    
    // Update UI to show disconnected state
    updateConnectionUI(null);
    
    // Add to connection errors log
    connectionErrors.push({
        time: new Date().toISOString(),
        type: 'WALLET_DISCONNECTED',
        message: 'Wallet was disconnected'
    });
}

/**
 * Update UI elements based on connection state
 * @param {string} account - Connected account address
 */
function updateConnectionUI(account) {
    walletLog("Updating UI for connection state", LOG_LEVELS.DEBUG, {
        account
    });
    
    const connectButton = document.getElementById('connect-wallet-btn');
    
    if (connectButton) {
        if (account) {
            // Format the address to show first 6 and last 4 characters
            const formattedAddress = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
            connectButton.textContent = formattedAddress;
            connectButton.classList.add('connected');
            
            // Add tooltip with full address
            connectButton.title = `Connected: ${account}`;
            
            walletLog("Updated UI to show connected state", LOG_LEVELS.DEBUG, {
                displayAddress: formattedAddress,
                fullAddress: account
            });
        } else {
            connectButton.textContent = 'Connect Wallet';
            connectButton.classList.remove('connected');
            connectButton.title = 'Connect to MetaMask';
            
            walletLog("Updated UI to show disconnected state", LOG_LEVELS.DEBUG);
        }
    } else {
        walletLog("Connect button not found in DOM", LOG_LEVELS.WARN);
    }
    
    // Update any other UI elements that depend on connection state
    // For example, you might want to show/hide certain elements based on connection state
    const connectedElements = document.querySelectorAll('.requires-wallet');
    const disconnectedElements = document.querySelectorAll('.requires-no-wallet');
    
    if (connectedElements.length > 0 || disconnectedElements.length > 0) {
        walletLog("Updating visibility of connection-dependent elements", LOG_LEVELS.DEBUG, {
            connectedElementsCount: connectedElements.length,
            disconnectedElementsCount: disconnectedElements.length
        });
        
        // Show/hide elements based on connection state
        connectedElements.forEach(el => {
            el.style.display = account ? '' : 'none';
        });
        
        disconnectedElements.forEach(el => {
            el.style.display = account ? 'none' : '';
        });
    }
}

/**
 * Initialize wallet connection
 * Sets up event listeners and checks for existing connection
 */
function initWalletConnection() {
    walletLog("Initializing wallet connection", LOG_LEVELS.INFO);
    
    // Set up connect wallet button
    const connectButton = document.getElementById('connect-wallet-btn');
    if (connectButton) {
        walletLog("Setting up connect wallet button", LOG_LEVELS.DEBUG);
        
        connectButton.addEventListener('click', async () => {
            walletLog("Connect wallet button clicked", LOG_LEVELS.INFO);
            
            // Check if already connected
            const isConnected = window.metamaskManager && 
                               window.metamaskManager.state.connectionState === 'CONNECTED';
            
            if (!isConnected) {
                walletLog("Attempting to connect wallet", LOG_LEVELS.INFO);
                const success = await connectWallet();
                
                if (success) {
                    walletLog("Connection successful, navigating to data selection", LOG_LEVELS.INFO);
                    // Navigate to data selection page after successful connection
                    window.location.href = '/web-app/data-selection.html';
                } else {
                    walletLog("Connection failed", LOG_LEVELS.WARN);
                }
            } else {
                walletLog("Already connected, navigating directly to data selection", LOG_LEVELS.INFO);
                // If already connected, navigate directly
                window.location.href = '/web-app/data-selection.html';
            }
        });
    } else {
        walletLog("Connect wallet button not found in DOM", LOG_LEVELS.WARN);
    }

    // Check if MetaMask Connection Manager is already loaded
    if (window.metamaskManager) {
        walletLog("MetaMask Connection Manager already loaded", LOG_LEVELS.INFO);
        
        // Check if already connected
        if (window.metamaskManager.state.connectionState === 'CONNECTED') {
            walletLog("Already connected to wallet", LOG_LEVELS.INFO, {
                account: window.metamaskManager.state.account,
                chainId: window.metamaskManager.state.chainId,
                balance: window.metamaskManager.state.balance
            });
            
            // Update UI to show connected state
            updateConnectionUI(window.metamaskManager.state.account);
            
            // Set up event listeners
            window.metamaskManager.on('onConnectionStateChanged', handleConnectionStateChanged);
            window.metamaskManager.on('onNetworkStateChanged', handleNetworkStateChanged);
            window.metamaskManager.on('onAccountChanged', handleAccountChanged);
            window.metamaskManager.on('onError', handleConnectionError);
        } else {
            walletLog("Not connected to wallet", LOG_LEVELS.INFO);
            
            // Update UI to show disconnected state
            updateConnectionUI(null);
        }
    } else {
        walletLog("MetaMask Connection Manager not loaded, will load on connect", LOG_LEVELS.INFO);
        
        // Update UI to show disconnected state
        updateConnectionUI(null);
    }
}

/**
 * Get the current wallet address
 * @returns {Promise<string>} Wallet address
 */
async function getWalletAddress() {
    walletLog("Getting wallet address", LOG_LEVELS.INFO);
    
    if (window.metamaskManager && window.metamaskManager.state.connectionState === 'CONNECTED') {
        return window.metamaskManager.state.account;
    } else {
        throw new Error('Wallet not connected');
    }
}

/**
 * Check if wallet is connected
 * @returns {Promise<boolean>} True if connected
 */
async function checkWalletConnection() {
    walletLog("Checking wallet connection", LOG_LEVELS.INFO);
    
    return window.metamaskManager && window.metamaskManager.state.connectionState === 'CONNECTED';
}

// Export functions for use in other files
window.walletFunctions = {
    connectWallet,
    disconnectWallet,
    isConnected: () => window.metamaskManager && window.metamaskManager.state.connectionState === 'CONNECTED',
    getCurrentAccount: () => window.metamaskManager ? window.metamaskManager.state.account : null,
    initWalletConnection,
    getWalletAddress,
    checkWalletConnection
};

// Also expose functions directly on window for easier access
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;
window.getWalletAddress = getWalletAddress;
window.checkWalletConnection = checkWalletConnection;

// Initialize wallet connection when the page loads
document.addEventListener('DOMContentLoaded', initWalletConnection);
