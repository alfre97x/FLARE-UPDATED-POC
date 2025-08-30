I met Flare team and knew about the solutions developed by Flare at ETH Oxford back in February 2025. I got a lot of interest in the network that I didn’t know about before and even if I didn’t build anything on Flare at that hackaton, I studied the technology and I wondered if it could be useful for my own project. //Spoiler: it was!//
As my personal project **not directly hackaton-related** I developed a system for satellites to more securely and exchange data among them and with the ground with more trust than currently. Such system will be launched in orbit by 2026 and I have various MoU already present.
However since I participated in the first webinar sessions of the hackaton, I fully understood that Flare could provide to my project an extra added value by creating with Flare a way to actually commercialize space data also on the ground (more is explained in the attached presentation: https://drive.google.com/file/d/1yT7lfIBMIgb-LRsZPIO6dgjjhjRmwhMd/view?usp=sharing ), by using FDC to actually as middleman between a potential client on the ground and a data source (currently Copernicus API working to select type of data and area of interest) , Flare blockchain for the payment of the data and VRF to simulate a random price value based on a simulated data demand. The satellite data (real not mocked ) from Copernicus is then passed to an AI assistant to analyze it.
Building with Flare put me in the situation to do web development after long time and challenged myself to make something that one day could generate profit while also having an impact and mix AI , blockchain and space.
You can find the contract here: https://coston2-explorer.flare.network/address/0x2330D0Cc23FD6764b7C67023C8fB85ae7287BFc9?tab=txs 



# SpaceData Purchase Application

This application allows users to purchase satellite data using blockchain technology, combining Copernicus satellite imagery with Flare Network blockchain verification.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   cd python_backend
   pip install -r requirements.txt
   ```
3. Configure environment variables in `.env` file (see Environment Variables section)

## Running the Application

To run the application:

```
.\start-python-server.bat  # Windows
./start-python-server.sh   # Linux/macOS
```

Then access the application at:
- http://localhost:5000

## Architecture

The application consists of a single Python backend that handles all functionality:

1. **Python Backend (Flask)**
   - Serves the UI
   - Handles Copernicus satellite data API
   - Provides AI analysis
   - Handles blockchain integration
   - Connects to Flare Network
   - Manages smart contracts

## Copernicus API Integration

The application integrates with the Copernicus Data Space Ecosystem (CDSE) to fetch satellite imagery:

- **Authentication**: Uses CDSE client credentials for API access
- **Data Search**: Searches for satellite data based on coordinates, date range, and data type
- **Image Retrieval**: Fetches satellite images from both STAC and OData APIs
- **Fallback Mechanisms**: Includes robust error handling and fallbacks between APIs

Key components:
- `python_backend/copernicus_api.py`: Core module for Copernicus API integration
- `python_backend/test_cdse.py` and `python_backend/test_stac_api.py`: Test scripts for API functionality

## Blockchain Integration

The application uses the Flare Network for blockchain functionality:

- **DataPurchase Contract**: Handles the purchase and verification of satellite data
- **FDC (Flare Data Consensus)**: Verifies the authenticity of satellite data through attestations
- **DA Layer API**: Provides access to attestation data and proofs
- **Price Randomization**: Generates random price variations (±10%) for satellite data purchases

For detailed information about the blockchain integration, see [BLOCKCHAIN_INTEGRATION.md](BLOCKCHAIN_INTEGRATION.md).

### Blockchain Components

- **Python Bridge**: `python_backend/blockchain_bridge.py` connects the Python backend to the blockchain
- **Python API**: `python_backend/blockchain_api.py` provides blockchain API endpoints
- **JavaScript Services**: `web-app/flare-services.js` provides blockchain functionality to the frontend
- **Smart Contracts**: Located in the `contracts/` directory
- **ABIs**: Located in the `abi/` directory
- **Scripts**: Located in the `scripts/` directory

## Flare Blockchain Technologies

The SpaceData application leverages three key Flare Network technologies:

### 1. Flare Data Consensus (FDC)

FDC is used to provide cryptographic verification of satellite data authenticity:

- **Key Files**:
  - `contracts/DataPurchase.sol` - Smart contract that interfaces with FDC Verification
  - `scripts/request_attestation.py` - Script to request attestations from FDC Hub
  - `scripts/oracle_manager.py` - Script to fetch and deliver attestation results
  - `python_backend/blockchain_api.py` - Backend API for FDC integration

- **Process Flow**:
  1. The application requests an attestation from the FDC Hub using `requestAttestation()`
  2. Flare validators reach consensus on the satellite data
  3. The attestation result is published to the DA Layer API
  4. Our oracle fetches the attestation result and proof
  5. The proof is verified using the FDC Verification contract
  6. The verified data is delivered to our DataPurchase contract

### 2. Smart Contracts

The application uses two main smart contracts:

1. **DataPurchase Contract** (`contracts/DataPurchase.sol`):
   - Handles the purchase of satellite data
   - Verifies data authenticity using FDC
   - Emits events for data requests and deliveries
   - Key functions:
     - `purchase(bytes32 requestId)` - Called by users to purchase data
     - `deliverData(bytes32 requestId, bytes32 attestationResponse, bytes proof)` - Called by the oracle to deliver verified data

2. **DataPurchaseRandomizer Contract** (`contracts/DataPurchaseRandomizer.sol`):
   - Interfaces with Flare's VRF for random number generation
   - Provides price randomization for satellite data purchases
   - Key functions:
     - `requestRandomness(bytes32 _userProvidedId)` - Requests random values from Flare VRF
     - `getRandomPriceVariation(bytes32 _userProvidedId, uint256 _basePrice, uint256 _variationPercent)` - Applies random variation to prices

### 3. Verifiable Random Function (VRF)

VRF is used to provide transparent, verifiable randomness for price variations:

- **Key Files**:
  - `contracts/DataPurchaseRandomizer.sol` - Contract that interfaces with Flare VRF
  - `web-app/flare-vrf.js` - Frontend service for VRF interactions
  - `web-app/pricing.js` - Uses VRF for price calculations
  - `space-data-app/services/flare/randomizer.js` - Mobile app service for VRF

- **Process Flow**:
  1. When a user views satellite data pricing, a request ID is generated
  2. The application requests randomness from Flare VRF
  3. VRF generates a verifiable random number
  4. The random number is used to apply a price variation (±10%)
  5. The final price is displayed to the user

## Complete Data Flow

1. **User Selects Data Parameters**:
   - User draws an area on the map
   - Selects date range and satellite type
   - Toggles AI analysis option

2. **Copernicus API Integration**:
   - Backend searches for satellite data matching parameters
   - Retrieves satellite images and metadata
   - Processes data for display

3. **Blockchain Transaction**:
   - Frontend generates a request ID
   - User connects wallet and confirms transaction
   - Smart contract records the purchase

4. **Verification Process**:
   - Backend requests attestation from FDC Hub
   - Oracle fetches attestation result and proof
   - Smart contract verifies the data integrity

5. **Results Display**:
   - Frontend displays satellite images
   - Shows transaction details and verification status
   - Provides AI analysis if requested

## Testing

### Testing the Copernicus API
To test the Copernicus API functionality:
```bash
python python_backend/test_cdse.py
python python_backend/test_stac_api.py
```

### Testing the Blockchain Integration
To test the blockchain integration:
```bash
# Windows
.\test-blockchain-integration.bat

# Linux/macOS
./test-blockchain-integration.sh
```

### Complete Integration Test
To test both the Copernicus API and blockchain integration together:
```bash
# Windows
.\test-integration.bat

# Linux/macOS
./test-integration.sh
```

This integration test will:
1. Check if the server is running
2. Test the Copernicus API search and data retrieval
3. Test the blockchain configuration and request ID generation

These scripts will:
1. Start the Python server
2. Test the blockchain API endpoints
3. Test the Python blockchain bridge
4. Open the blockchain test page in your browser

## Smart Contracts

The smart contracts are located in the `contracts/` directory:

- `DataPurchase.sol`: Main contract for purchasing satellite data
- `DataPurchaseRandomizer.sol`: Contract for generating random price variations

## Environment Variables

The application uses environment variables for configuration:

### Blockchain Configuration
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

### Copernicus API Configuration
```
# CDSE API credentials
CDSE_CLIENT_ID=your_client_id_here
CDSE_CLIENT_SECRET=your_client_secret_here
```

## Troubleshooting

If you encounter issues:

1. Make sure the Python server is running
2. Check the console for errors
3. Ensure MetaMask is installed and connected to Flare Coston2 Testnet
4. Verify that the contract addresses in `.env` are correct
5. Check that the Python backend can connect to the blockchain network
6. Verify your Copernicus API credentials if satellite images aren't loading
7. Check network connectivity to both Flare Network and Copernicus API servers
