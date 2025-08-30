# SpaceData Purchase Application

A web application that allows users to purchase satellite data using blockchain technology, combining Copernicus satellite imagery with Flare Network blockchain verification.

## Features

- **Satellite Data Selection**: Search and select satellite data based on location, date range, and data type
- **Blockchain Verification**: Verify the authenticity of satellite data using Flare Data Consensus (FDC)
- **AI Analysis**: Analyze satellite data using AI to extract insights
- **Price Randomization**: Generate random price variations using Flare's Verifiable Random Function (VRF)
- **MetaMask Integration**: Connect to the Flare Network using MetaMask

## Architecture

The application consists of a Python backend that handles all functionality:

1. **Python Backend (Flask)**
   - Serves the UI
   - Handles Copernicus satellite data API
   - Provides AI analysis
   - Handles blockchain integration
   - Connects to Flare Network
   - Manages smart contracts

## Setup

### Prerequisites

- Python 3.8 or higher
- Node.js and npm (for Hardhat)
- Git
- MetaMask browser extension
- Flare Coston2 Testnet account with test FLR tokens

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/alfre97x/hackaton-flare-april.git
   cd hackaton-flare-april
   ```

2. Install Python dependencies:
   ```
   cd python_backend
   pip install -r requirements.txt
   cd ..
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your own values for the environment variables

### Running the Application

To run the application:

```
# Windows
start-python-server.bat

# Linux/macOS
./start-python-server.sh
```

Then access the application at:
- http://localhost:5000

## Blockchain Integration

The application uses the Flare Network for blockchain functionality:

### Flare Data Consensus (FDC)

FDC is used to provide cryptographic verification of satellite data authenticity:

- **Process Flow**:
  1. The application requests an attestation from the FDC Hub
  2. Flare validators reach consensus on the satellite data
  3. The attestation result is published to the DA Layer API
  4. Our oracle fetches the attestation result and proof
  5. The proof is verified using the FDC Verification contract
  6. The verified data is delivered to our DataPurchase contract

### Smart Contracts

The application uses two main smart contracts:

1. **DataPurchase Contract** (`contracts/DataPurchase.sol`):
   - Handles the purchase of satellite data
   - Verifies data authenticity using FDC
   - Emits events for data requests and deliveries

2. **DataPurchaseRandomizer Contract** (`contracts/DataPurchaseRandomizer.sol`):
   - Interfaces with Flare's VRF for random number generation
   - Provides price randomization for satellite data purchases

### Verifiable Random Function (VRF)

VRF is used to provide transparent, verifiable randomness for price variations:

- **Process Flow**:
  1. When a user views satellite data pricing, a request ID is generated
  2. The application requests randomness from Flare VRF
  3. VRF generates a verifiable random number
  4. The random number is used to apply a price variation (±10%)
  5. The final price is displayed to the user

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

### AI API Configuration
```
# AI API credentials
AI_API_KEY=your_openai_api_key_here
```

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
test-blockchain-integration.bat

# Linux/macOS
./test-blockchain-integration.sh
```

### Complete Integration Test
To test both the Copernicus API and blockchain integration together:
```bash
# Windows
test-integration.bat

# Linux/macOS
./test-integration.sh
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flare Network for providing the blockchain infrastructure
- Copernicus Data Space Ecosystem for providing satellite data
- OpenAI for providing AI capabilities
