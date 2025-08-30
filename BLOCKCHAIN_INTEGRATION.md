# Blockchain Integration for SpaceData Application

This document outlines the integration of Flare blockchain functionality into the SpaceData application, focusing on the Flare Data Contract (FDC) and oracle system for verified satellite data delivery.

## Architecture Overview

The blockchain integration consists of several components:

1. **Smart Contracts**:
   - `DataPurchase.sol`: Handles the purchase and delivery of satellite data
   - FDC Hub (external): Manages attestation requests
   - FDC Verification (external): Verifies attestations

2. **Backend Services**:
   - `blockchain_api.py`: Provides blockchain functionality to the Python backend
   - `blockchain_bridge.py`: Exposes blockchain API endpoints for the frontend

3. **Frontend Components**:
   - `flare-services.js`: JavaScript library for interacting with blockchain contracts
   - `wallet.js`: Handles wallet connection and transaction signing
   - `metamask-connection.js`: Manages MetaMask wallet connection

4. **Scripts**:
   - `request_attestation.py`: Requests attestations from the FDC Hub
   - `oracle_manager.py`: Fetches and delivers attestation results

## Data Flow

The blockchain integration follows this flow:

1. **User Initiates Data Request**:
   - User selects satellite data parameters (coordinates, time range, etc.)
   - Frontend generates a request ID based on these parameters
   - User connects their wallet and submits a purchase transaction

2. **Backend Processes Request**:
   - Backend receives the purchase event
   - Queries Copernicus API for the requested satellite data
   - Generates a hash of the result metadata
   - Submits an attestation request to the FDC Hub

3. **Oracle Delivers Verification**:
   - Oracle monitors for attestation requests
   - Fetches attestation results from the DA Layer API
   - Delivers the verified data to the DataPurchase contract

4. **User Receives Verified Data**:
   - Frontend listens for DataDelivered events
   - Displays the verified satellite data and blockchain transaction details

## Smart Contract Details

### DataPurchase Contract

The DataPurchase contract handles the purchase and delivery of satellite data:

- `purchase(bytes32 requestId)`: Called by users to purchase data
- `deliverData(bytes32 requestId, bytes32 attestationResponse, bytes proof)`: Called by the oracle to deliver verified data
- Events:
  - `DataRequested(address buyer, bytes32 requestId)`
  - `DataDelivered(bytes32 requestId, bytes32 dataHash)`

## Integration Points

### Python Backend

The Python backend integrates with the blockchain through:

1. **Blockchain API**:
   - `get_config()`: Returns blockchain configuration
   - `request_attestation()`: Requests attestation from FDC Hub
   - `fetch_attestation_result()`: Fetches attestation result from DA Layer API
   - `verify_attestation()`: Verifies attestation using FDC Verification contract
   - `deliver_data()`: Delivers data to DataPurchase contract
   - `generate_request_id()`: Generates a request ID for a data request

2. **Blockchain Bridge**:
   - Exposes RESTful API endpoints for the frontend
   - Handles authentication and request validation
   - Manages blockchain transaction state

### Frontend

The frontend integrates with the blockchain through:

1. **Flare Services**:
   - `initializeBlockchain()`: Initializes blockchain connection
   - `purchaseData()`: Purchases data using the DataPurchase contract
   - `requestAttestation()`: Requests attestation from FDC Hub
   - `fetchAttestationResult()`: Fetches attestation result from DA Layer API
   - `verifyAttestation()`: Verifies attestation using FDC Verification contract
   - `deliverData()`: Delivers data to DataPurchase contract

2. **Wallet Connection**:
   - Handles MetaMask connection
   - Manages account state
   - Signs transactions

## Configuration

The blockchain integration is configured through environment variables in the `.env` file:

```
# Blockchain connection
RPC_URL=https://coston2-api.flare.network/ext/C/rpc
PRIVATE_KEY=your_private_key_here

# Smart contracts
DATAPURCHASE_CONTRACT_ADDRESS=your_deployed_contract_address
FDC_HUB_ADDRESS=0x48aC463d797582898331F4De43341627b9c5f1D
FDC_VERIFICATION_ADDRESS=0x075bf3f01fF07C4920e5261F9a366969640F5348

# Flare DA Layer API
DA_LAYER_API=https://api.da.coston2.flare.network
```

## Testing

The blockchain integration can be tested using:

1. **Unit Tests**:
   - Test individual blockchain functions
   - Mock blockchain responses

2. **Integration Tests**:
   - Test the full data flow from purchase to delivery
   - Use the Flare Coston2 testnet

3. **Manual Testing**:
   - Use the web interface to purchase data
   - Monitor blockchain transactions
   - Verify data delivery

## Deployment

To deploy the blockchain integration:

1. **Deploy Smart Contracts**:
   - Use Remix or Hardhat to deploy the DataPurchase contract
   - Update the contract address in the `.env` file

2. **Configure Backend**:
   - Set up environment variables
   - Install required Python packages

3. **Configure Frontend**:
   - Update contract addresses
   - Set up MetaMask connection

## Security Considerations

The blockchain integration includes several security measures:

1. **Private Key Management**:
   - Private keys are stored in environment variables
   - Backend uses secure key management

2. **Transaction Validation**:
   - All transactions are validated before submission
   - Smart contract includes access controls

3. **Error Handling**:
   - Robust error handling for blockchain operations
   - Fallback mechanisms for failed transactions

## Future Improvements

Potential improvements to the blockchain integration:

1. **Multi-Chain Support**:
   - Support for additional Flare networks
   - Integration with other EVM-compatible chains

2. **Enhanced Oracle System**:
   - Decentralized oracle network
   - Redundant data sources

3. **Advanced Payment Models**:
   - Subscription-based access
   - Pay-per-use pricing
   - Token-based incentives
