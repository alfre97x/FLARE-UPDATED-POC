/**
 * MetaMask Connection Manager
 * A robust utility for handling MetaMask wallet connections and transactions
 */

// Connection states
const CONNECTION_STATES = {
    NOT_INSTALLED: 'NOT_INSTALLED',
    DISCONNECTED: 'DISCONNECTED',
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    ERROR: 'ERROR'
};

// Network states
const NETWORK_STATES = {
    UNKNOWN: 'UNKNOWN',
    WRONG_NETWORK: 'WRONG_NETWORK',
    CORRECT_NETWORK: 'CORRECT_NETWORK',
    SWITCHING: 'SWITCHING'
};

// Flare Network configuration (Coston2 Testnet)
const FLARE_NETWORK_PARAMS = {
    chainId: '0x72', // Chain ID for Coston2 Testnet (114 in decimal)
    chainName: 'Coston2 Testnet',
    nativeCurrency: {
        name: 'Coston2 Flare',
        symbol: 'C2FLR',
        decimals: 18
    },
    rpcUrls: ['https://coston2-api.flare.network/ext/C/rpc'],
    blockExplorerUrls: ['https://coston2-explorer.flare.network']
};

// MetaMask Connection Manager Class
class MetaMaskConnectionManager {
    constructor(options = {}) {
        // Configuration options
        this.options = {
            autoConnect: false,
            requiredNetwork: FLARE_NETWORK_PARAMS.chainId,
            autoSwitchNetwork: true,
            connectionTimeout: 10000, // 10 seconds
            debug: true,
            ...options
        };
        
        // State
        this.state = {
            connectionState: CONNECTION_STATES.DISCONNECTED,
            networkState: NETWORK_STATES.UNKNOWN,
            account: null,
            chainId: null,
            balance: null,
            error: null,
            isMetaMaskInstalled: false,
            connectionAttempts: 0,
            lastConnectionTime: null
        };
        
        // Event listeners
        this.eventListeners = {
            onConnectionStateChanged: [],
            onNetworkStateChanged: [],
            onAccountChanged: [],
            onError: []
        };
        
        // Timeouts and intervals
        this.timeouts = {
            connectionTimeout: null,
            networkSwitchTimeout: null
        };
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the connection manager
     */
    initialize() {
        this.log('Initializing MetaMask Connection Manager');
        
        // Check if MetaMask is installed
        this.checkMetaMaskInstallation();
        
        // Set up event listeners for MetaMask
        this.setupEventListeners();
        
        // Auto-connect if enabled
        if (this.options.autoConnect && this.state.isMetaMaskInstalled) {
            this.connect();
        }
    }
    
    /**
     * Check if MetaMask is installed
     * @returns {boolean} True if MetaMask is installed
     */
    checkMetaMaskInstallation() {
        this.log('Checking for MetaMask installation');
        
        // Check if ethereum object exists
        const hasEthereum = typeof window.ethereum !== 'undefined';
        
        // Check if it's actually MetaMask
        const isMetaMask = hasEthereum && window.ethereum.isMetaMask;
        
        this.state.isMetaMaskInstalled = isMetaMask;
        
        if (!isMetaMask) {
            this.state.connectionState = CONNECTION_STATES.NOT_INSTALLED;
            this.state.error = 'MetaMask is not installed';
            this.triggerEvent('onConnectionStateChanged', this.state);
            this.triggerEvent('onError', { message: 'MetaMask is not installed' });
        }
        
        this.log(`MetaMask installed: ${isMetaMask}`);
        return isMetaMask;
    }
    
    /**
     * Set up event listeners for MetaMask
     */
    setupEventListeners() {
        if (!this.state.isMetaMaskInstalled) {
            return;
        }
        
        this.log('Setting up MetaMask event listeners');
        
        // Account changed event
        window.ethereum.on('accountsChanged', (accounts) => {
            this.log('MetaMask accounts changed', accounts);
            
            if (accounts.length === 0) {
                // User disconnected their wallet
                this.state.connectionState = CONNECTION_STATES.DISCONNECTED;
                this.state.account = null;
                this.state.balance = null;
                this.triggerEvent('onConnectionStateChanged', this.state);
                this.triggerEvent('onAccountChanged', null);
            } else {
                // User switched accounts
                this.state.account = accounts[0];
                this.getAccountBalance();
                this.triggerEvent('onAccountChanged', accounts[0]);
            }
        });
        
        // Chain changed event
        window.ethereum.on('chainChanged', (chainId) => {
            this.log('MetaMask chain changed', chainId);
            
            this.state.chainId = chainId;
            
            // Check if the new chain is the required network
            const isCorrectNetwork = chainId === this.options.requiredNetwork;
            
            this.state.networkState = isCorrectNetwork ? 
                NETWORK_STATES.CORRECT_NETWORK : 
                NETWORK_STATES.WRONG_NETWORK;
            
            this.triggerEvent('onNetworkStateChanged', this.state.networkState);
            
            // Auto-switch network if enabled
            if (!isCorrectNetwork && this.options.autoSwitchNetwork) {
                this.switchToRequiredNetwork();
            }
        });
        
        // Connection event
        window.ethereum.on('connect', (connectInfo) => {
            this.log('MetaMask connected', connectInfo);
            
            this.state.chainId = connectInfo.chainId;
            
            // Check if the connected chain is the required network
            const isCorrectNetwork = connectInfo.chainId === this.options.requiredNetwork;
            
            this.state.networkState = isCorrectNetwork ? 
                NETWORK_STATES.CORRECT_NETWORK : 
                NETWORK_STATES.WRONG_NETWORK;
            
            this.triggerEvent('onNetworkStateChanged', this.state.networkState);
        });
        
        // Disconnect event
        window.ethereum.on('disconnect', (error) => {
            this.log('MetaMask disconnected', error);
            
            this.state.connectionState = CONNECTION_STATES.DISCONNECTED;
            this.state.account = null;
            this.state.balance = null;
            this.state.error = error;
            
            this.triggerEvent('onConnectionStateChanged', this.state);
            this.triggerEvent('onError', error);
        });
    }
    
    /**
     * Connect to MetaMask
     * @returns {Promise<boolean>} True if connection successful
     */
    async connect() {
        if (!this.state.isMetaMaskInstalled) {
            this.state.error = 'MetaMask is not installed';
            this.triggerEvent('onError', { message: 'MetaMask is not installed' });
            return false;
        }
        
        // Prevent multiple connection attempts
        if (this.state.connectionState === CONNECTION_STATES.CONNECTING) {
            this.log('Already connecting to MetaMask');
            return false;
        }
        
        this.log('Connecting to MetaMask');
        
        // Update state
        this.state.connectionState = CONNECTION_STATES.CONNECTING;
        this.state.connectionAttempts++;
        this.state.lastConnectionTime = Date.now();
        this.state.error = null;
        
        this.triggerEvent('onConnectionStateChanged', this.state);
        
        // Set connection timeout
        this.timeouts.connectionTimeout = setTimeout(() => {
            if (this.state.connectionState === CONNECTION_STATES.CONNECTING) {
                this.state.connectionState = CONNECTION_STATES.ERROR;
                this.state.error = 'Connection timeout';
                this.triggerEvent('onConnectionStateChanged', this.state);
                this.triggerEvent('onError', { message: 'Connection timeout' });
            }
        }, this.options.connectionTimeout);
        
        try {
            // Request accounts
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            
            // Clear timeout
            clearTimeout(this.timeouts.connectionTimeout);
            
            if (accounts.length > 0) {
                // Update state
                this.state.connectionState = CONNECTION_STATES.CONNECTED;
                this.state.account = accounts[0];
                
                // Get chain ID
                const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                this.state.chainId = chainId;
                
                // Check if the connected chain is the required network
                const isCorrectNetwork = chainId === this.options.requiredNetwork;
                
                this.state.networkState = isCorrectNetwork ? 
                    NETWORK_STATES.CORRECT_NETWORK : 
                    NETWORK_STATES.WRONG_NETWORK;
                
                // Get account balance
                await this.getAccountBalance();
                
                this.triggerEvent('onConnectionStateChanged', this.state);
                this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                this.triggerEvent('onAccountChanged', this.state.account);
                
                // Auto-switch network if enabled
                if (!isCorrectNetwork && this.options.autoSwitchNetwork) {
                    await this.switchToRequiredNetwork();
                }
                
                return true;
            } else {
                // No accounts found
                this.state.connectionState = CONNECTION_STATES.ERROR;
                this.state.error = 'No accounts found';
                
                this.triggerEvent('onConnectionStateChanged', this.state);
                this.triggerEvent('onError', { message: 'No accounts found' });
                
                return false;
            }
        } catch (error) {
            // Clear timeout
            clearTimeout(this.timeouts.connectionTimeout);
            
            // Handle user rejection
            if (error.code === 4001) {
                this.state.connectionState = CONNECTION_STATES.DISCONNECTED;
                this.state.error = 'User rejected the connection request';
            } else {
                this.state.connectionState = CONNECTION_STATES.ERROR;
                this.state.error = error.message || 'Unknown error';
            }
            
            this.triggerEvent('onConnectionStateChanged', this.state);
            this.triggerEvent('onError', error);
            
            this.log('Error connecting to MetaMask', error);
            return false;
        }
    }
    
    /**
     * Disconnect from MetaMask
     */
    disconnect() {
        this.log('Disconnecting from MetaMask');
        
        // Update state
        this.state.connectionState = CONNECTION_STATES.DISCONNECTED;
        this.state.account = null;
        this.state.balance = null;
        
        this.triggerEvent('onConnectionStateChanged', this.state);
        this.triggerEvent('onAccountChanged', null);
    }
    
    /**
     * Get account balance
     * @returns {Promise<string>} Account balance in ETH
     */
    async getAccountBalance() {
        if (!this.state.account) {
            return null;
        }
        
        try {
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [this.state.account, 'latest']
            });
            
            // Convert from wei to ETH
            const balanceInEth = parseInt(balance, 16) / 1e18;
            this.state.balance = balanceInEth;
            
            return balanceInEth;
        } catch (error) {
            this.log('Error getting account balance', error);
            return null;
        }
    }
    
    /**
     * Switch to the required network
     * @returns {Promise<boolean>} True if switch successful
     */
    async switchToRequiredNetwork() {
        if (!this.state.isMetaMaskInstalled || !this.state.account) {
            return false;
        }
        
        this.log('Switching to required network', this.options.requiredNetwork);
        
        // Update state
        this.state.networkState = NETWORK_STATES.SWITCHING;
        this.triggerEvent('onNetworkStateChanged', this.state.networkState);
        
        try {
            // Try to switch to the network
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: this.options.requiredNetwork }]
            });
            
            // Update state
            this.state.networkState = NETWORK_STATES.CORRECT_NETWORK;
            this.triggerEvent('onNetworkStateChanged', this.state.networkState);
            
            return true;
        } catch (error) {
            // This error code indicates that the chain has not been added to MetaMask
            if (error.code === 4902) {
                try {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [FLARE_NETWORK_PARAMS]
                    });
                    
                    // Check if the switch was successful
                    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                    
                    if (chainId === this.options.requiredNetwork) {
                        this.state.networkState = NETWORK_STATES.CORRECT_NETWORK;
                        this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                        return true;
                    } else {
                        this.state.networkState = NETWORK_STATES.WRONG_NETWORK;
                        this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                        return false;
                    }
                } catch (addError) {
                    this.state.networkState = NETWORK_STATES.WRONG_NETWORK;
                    this.state.error = addError.message || 'Failed to add network';
                    
                    this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                    this.triggerEvent('onError', addError);
                    
                    return false;
                }
            } else if (error.code === 4001) {
                // User rejected the request
                this.state.networkState = NETWORK_STATES.WRONG_NETWORK;
                this.state.error = 'User rejected the request to switch networks';
                
                this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                this.triggerEvent('onError', error);
                
                return false;
            } else {
                this.state.networkState = NETWORK_STATES.WRONG_NETWORK;
                this.state.error = error.message || 'Failed to switch network';
                
                this.triggerEvent('onNetworkStateChanged', this.state.networkState);
                this.triggerEvent('onError', error);
                
                return false;
            }
        }
    }
    
    /**
     * Send a transaction
     * @param {Object} transactionParameters Transaction parameters
     * @returns {Promise<string>} Transaction hash
     */
    async sendTransaction(transactionParameters) {
        if (!this.state.isMetaMaskInstalled || !this.state.account) {
            throw new Error('MetaMask not connected');
        }
        
        // Check if on the correct network
        if (this.state.networkState !== NETWORK_STATES.CORRECT_NETWORK) {
            // Try to switch to the correct network
            const switched = await this.switchToRequiredNetwork();
            
            if (!switched) {
                throw new Error('Not connected to the required network');
            }
        }
        
        this.log('Sending transaction', transactionParameters);
        
        try {
            // Ensure the 'from' address is set to the current account
            const params = {
                ...transactionParameters,
                from: this.state.account
            };
            
            // Send the transaction
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [params]
            });
            
            this.log('Transaction sent', txHash);
            return txHash;
        } catch (error) {
            this.log('Error sending transaction', error);
            
            // Trigger error event
            this.triggerEvent('onError', error);
            
            throw error;
        }
    }
    
    /**
     * Call a contract function (read-only)
     * @param {Object} callParameters Call parameters
     * @returns {Promise<any>} Call result
     */
    async callContract(callParameters) {
        if (!this.state.isMetaMaskInstalled) {
            throw new Error('MetaMask not connected');
        }
        
        this.log('Calling contract', callParameters);
        
        try {
            // Ensure the 'from' address is set to the current account if available
            const params = {
                ...callParameters,
                from: this.state.account || undefined
            };
            
            // Call the contract
            const result = await window.ethereum.request({
                method: 'eth_call',
                params: [params, 'latest']
            });
            
            this.log('Contract call result', result);
            return result;
        } catch (error) {
            this.log('Error calling contract', error);
            
            // Trigger error event
            this.triggerEvent('onError', error);
            
            throw error;
        }
    }
    
    /**
     * Add event listener
     * @param {string} event Event name
     * @param {Function} callback Callback function
     */
    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }
    
    /**
     * Remove event listener
     * @param {string} event Event name
     * @param {Function} callback Callback function
     */
    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }
    
    /**
     * Trigger event
     * @param {string} event Event name
     * @param {any} data Event data
     */
    triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} event listener:`, error);
                }
            });
        }
    }
    
    /**
     * Log message
     * @param {string} message Message
     * @param {any} data Additional data
     */
    log(message, data) {
        if (this.options.debug) {
            const timestamp = new Date().toISOString();
            const prefix = `[MetaMask ${timestamp}]`;
            
            if (data) {
                console.log(`${prefix} ${message}`, data);
            } else {
                console.log(`${prefix} ${message}`);
            }
        }
    }
    
    /**
     * Get current state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }
}

// Create a global instance
window.metamaskManager = new MetaMaskConnectionManager();

// Export the class and constants
window.MetaMaskConnectionManager = {
    Manager: MetaMaskConnectionManager,
    CONNECTION_STATES,
    NETWORK_STATES,
    FLARE_NETWORK_PARAMS
};
