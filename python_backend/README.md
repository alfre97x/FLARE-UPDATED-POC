


# SpaceData Python Backend

This is a Flask-based backend for the SpaceData application. It provides API endpoints for accessing Copernicus satellite data and integrates with the Flare blockchain for data verification.

## Features

- Secure API proxy for Copernicus Data Space Ecosystem (CDSE)
- Authentication with CDSE API
- Search for satellite data based on criteria
- Retrieve satellite imagery and metadata
- Blockchain integration for data purchase and verification
- AI analysis of satellite imagery
- Serve static files from the web application

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- MetaMask or other Web3 wallet (for blockchain features)

## Installation

1. Clone the repository (if you haven't already)

2. Navigate to the python_backend directory:
   ```
   cd python_backend
   ```

3. Create a virtual environment (recommended):
   ```
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Make sure the environment variables are set in the `.env` file at the root of the project:
   ```
   # Copernicus API credentials
   CDSE_CLIENT_ID=your-client-id
   CDSE_CLIENT_SECRET=your-client-secret
   
   # Blockchain connection
   RPC_URL=https://coston2-api.flare.network/ext/C/rpc
   PRIVATE_KEY=your-private-key-here
   
   # Smart contracts
   DATAPURCHASE_CONTRACT_ADDRESS=your-deployed-contract-address
   FDC_HUB_ADDRESS=0x48aC463d797582898331F4De43341627b9c5f1D
   FDC_VERIFICATION_ADDRESS=0x075bf3f01fF07C4920e5261F9a366969640F5348
   
   # Flare DA Layer API
   DA_LAYER_API=https://api.da.coston2.flare.network
   
   # Server configuration
   PORT=5000
   ```

## Running the Server

1. Make sure your virtual environment is activated

2. Start the server:
   ```
   python app.py
   ```

3. The server will start on http://localhost:5000 (or the port specified in your .env file)

## Key Components

### Copernicus API Integration

- `copernicus_api.py`: Core module for interacting with the Copernicus Data Space Ecosystem
  - Authentication with CDSE API
  - Search for satellite data
  - Retrieve satellite imagery and metadata
  - Fallback mechanisms between STAC and OData APIs

### Blockchain Integration

- `blockchain_bridge.py`: Flask blueprint for blockchain API endpoints
- `blockchain_api.py`: Core module for blockchain functionality
  - Connect to Flare Network
  - Generate request IDs
  - Request attestations
  - Verify attestations
  - Deliver data to smart contracts

### Web Interface

- `templates/`: HTML templates for the web interface
  - `index.html`: Home page
  - `data_selection.html`: Data selection page
  - `data_results.html`: Data results page
  - `blockchain-test.html`: Blockchain testing page

## API Endpoints

### Copernicus API Endpoints

- **Search for Satellite Data**
  - **URL**: `/api/copernicus/search`
  - **Method**: `POST`
  - **Body**:
    ```json
    {
      "dataType": "S2MSI2A",
      "coordinates": [[41.3, 2.1], [41.3, 2.3], [41.5, 2.3], [41.5, 2.1]],
      "startDate": "2023-04-15",
      "endDate": "2023-04-22"
    }
    ```
  - **Response**: List of satellite data products matching the criteria

- **Get Product Preview**
  - **URL**: `/api/copernicus/product/{productId}/preview`
  - **Method**: `GET`
  - **Response**: Preview image for the specified product

- **Get Product Metadata**
  - **URL**: `/api/copernicus/product/{productId}/metadata`
  - **Method**: `GET`
  - **Response**: Metadata for the specified product

- **Get Product Data**
  - **URL**: `/api/copernicus/product/{productId}`
  - **Method**: `GET`
  - **Response**: Combined data including metadata and preview image

### Blockchain API Endpoints

- **Generate Request ID**
  - **URL**: `/api/blockchain/generate-request-id`
  - **Method**: `POST`
  - **Body**:
    ```json
    {
      "data_info": {
        "dataType": "S2MSI2A",
        "startDate": "2023-04-15",
        "endDate": "2023-04-22",
        "coordinates": "[[41.3, 2.1], [41.3, 2.3], [41.5, 2.3], [41.5, 2.1]]",
        "aiAnalysis": true
      }
    }
    ```
  - **Response**: Request ID for the data purchase

- **Get Blockchain Configuration**
  - **URL**: `/api/blockchain/config`
  - **Method**: `GET`
  - **Response**: Blockchain configuration including contract addresses

## Testing

### Testing the Copernicus API

To test the Copernicus API functionality:

```bash
python test_cdse.py
python test_stac_api.py
```

### Testing the Blockchain Integration

To test the blockchain integration:

```bash
python test_blockchain_bridge.py
```

## Development

- The server runs in debug mode by default, which provides detailed error messages and auto-reloads when code changes
- Logs are printed to the console with timestamps and log levels
- CORS is enabled for all routes to allow cross-origin requests from the frontend

## Troubleshooting

- If you encounter CORS issues, make sure the frontend is making requests to the correct backend URL
- If authentication fails, check your CDSE credentials in the .env file
- If blockchain transactions fail, check your RPC URL and private key in the .env file
- For other issues, check the server logs for detailed error messages
