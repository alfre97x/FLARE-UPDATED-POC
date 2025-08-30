/**
 * Blockchain Controller
 * Handles blockchain-related API requests
 */

const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

/**
 * Get blockchain configuration
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
exports.getBlockchainConfig = (req, res) => {
    try {
        // Get contract addresses from environment variables
        const dataPurchaseContractAddress = process.env.DATAPURCHASE_CONTRACT_ADDRESS;
        const fdcHubAddress = process.env.FDC_HUB_ADDRESS;
        const fdcVerificationAddress = process.env.FDC_VERIFICATION_ADDRESS;
        
        // Build chain/network configuration (supports dynamic networks, e.g. Coston3)
        // Normalize CHAIN_ID to 0x-prefixed lowercase hex as required by MetaMask
        const rawChainId = process.env.CHAIN_ID || '0x72';
        const chainId = (rawChainId.toString().startsWith('0x') ? rawChainId : '0x' + parseInt(rawChainId, 10).toString(16)).toLowerCase();
        const chainName = process.env.CHAIN_NAME || 'Coston2 Testnet';
        const blockExplorerUrl = process.env.BLOCK_EXPLORER_URL || 'https://coston2-explorer.flare.network';
        const nativeCurrency = {
            name: process.env.NATIVE_CURRENCY_NAME || 'Coston2 Flare',
            symbol: process.env.NATIVE_CURRENCY_SYMBOL || 'C2FLR',
            decimals: parseInt(process.env.NATIVE_CURRENCY_DECIMALS || '18', 10)
        };

        // Return configuration
        res.json({
            dataPurchaseContractAddress,
            fdcHubAddress,
            fdcVerificationAddress,
            dataPurchaseRandomizerAddress: process.env.DATAPURCHASE_RANDOMIZER_ADDRESS,
            rpcUrl: process.env.RPC_URL,
            daLayerApi: process.env.DA_LAYER_API,
            chainId,
            chainName,
            blockExplorerUrls: [blockExplorerUrl],
            nativeCurrency
        });
    } catch (error) {
        console.error('Error getting blockchain config:', error);
        res.status(500).json({ error: 'Failed to get blockchain configuration' });
    }
};

/**
 * Verify blockchain attestation
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
exports.verifyAttestation = async (req, res) => {
    try {
        const { requestId } = req.body;
        
        if (!requestId) {
            return res.status(400).json({ error: 'Missing requestId parameter' });
        }
        
        // For now, return a mock verification result
        // In a real implementation, this would call the Python backend
        const mockResult = {
            verified: Math.random() > 0.5, // Randomly return true or false
            status: Math.random() > 0.5 ? 'verified' : 'pending',
            message: 'Attestation verification result',
            attestationResponse: `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`,
            proof: `0x${Array(128).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`
        };
        
        res.json(mockResult);
    } catch (error) {
        console.error('Error verifying attestation:', error);
        res.status(500).json({ error: 'Failed to verify attestation' });
    }
};

/**
 * Purchase satellite data
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
exports.purchaseData = async (req, res) => {
    try {
        const { dataType, coordinates, startDate, endDate, price } = req.body;
        
        // Validate required parameters
        if (!dataType) {
            return res.status(400).json({ error: 'Missing required parameter: dataType' });
        }
        
        if (!startDate || !endDate) {
            return res.status(400).json({ error: 'Missing required parameters: startDate or endDate' });
        }
        
        // Generate a mock request ID
        const requestId = `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`;
        
        // Generate a mock transaction hash
        const transactionHash = `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`;
        
        // Generate a mock attestation transaction hash
        const attestationTransactionHash = `0x${Array(64).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join('')}`;
        
        // Return mock result
        // In a real implementation, this would call the Python backend
        res.json({
            success: true,
            requestId,
            transactionHash,
            attestationTransactionHash,
            message: 'Data purchase request submitted successfully'
        });
    } catch (error) {
        console.error('Error purchasing data:', error);
        res.status(500).json({ error: 'Failed to purchase data' });
    }
};
