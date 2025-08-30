# Flare Blockchain Scripts

This directory contains scripts for interacting with the Flare blockchain and the SpaceData application's smart contracts.

## Scripts

- `request_attestation.py`: Requests an attestation from the Flare Data Contract (FDC) Hub for satellite data.
- `oracle_manager.py`: Fetches attestation results from the Flare DA Layer API and delivers them to the DataPurchase contract.

## Usage

### Prerequisites

Before running these scripts, make sure you have:

1. Python 3.7+ installed
2. Required Python packages installed:
   ```
   pip install web3 requests python-dotenv
   ```
3. A `.env` file in the project root with the following variables:
   ```
   RPC_URL=https://coston2-api.flare.network/ext/C/rpc
   PRIVATE_KEY=your_private_key_here
   DATAPURCHASE_CONTRACT_ADDRESS=your_deployed_contract_address
   FDC_HUB_ADDRESS=0x48aC463d797582898331F4De43341627b9c5f1D
   FDC_VERIFICATION_ADDRESS=0x075bf3f01fF07C4920e5261F9a366969640F5348
   DA_LAYER_API=https://api.da.coston2.flare.network
   ```

### Running the Scripts

#### Request Attestation

To request an attestation for satellite data:

```bash
python scripts/request_attestation.py
```

This will:
1. Connect to the Flare Coston2 testnet
2. Request an attestation from the FDC Hub
3. Print the transaction hash

#### Oracle Manager

To fetch an attestation result and deliver it to the DataPurchase contract:

```bash
python scripts/oracle_manager.py
```

This will:
1. Connect to the Flare Coston2 testnet
2. Generate a request ID (in a real scenario, this would be provided)
3. Wait for the attestation to be processed
4. Fetch the attestation result from the DA Layer API
5. Deliver the result to the DataPurchase contract
6. Print the transaction hash

## Customization

You can modify these scripts to fit your specific use case:

- In `request_attestation.py`, change the `attestation_type` and `parameters` variables to match your data requirements.
- In `oracle_manager.py`, replace the example request ID generation with your actual request ID handling logic.

## Integration with Web Application

These scripts can be integrated with the web application by:

1. Creating API endpoints that trigger these scripts
2. Using the same Web3 logic in JavaScript for the frontend
3. Setting up a background job to monitor for attestation requests and deliver results
