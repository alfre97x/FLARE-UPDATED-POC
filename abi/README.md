
# Flare Blockchain ABI Files

This directory contains the ABI (Application Binary Interface) files for the smart contracts used in the SpaceData application.

## Files

- `datapurchase_abi.json`: ABI for the DataPurchase contract, which handles the purchase and delivery of satellite data.
- `fdc_hub_abi.json`: ABI for the Flare Data Contract (FDC) Hub, which handles attestation requests.
- `fdc_verification_abi.json`: ABI for the FDC Verification contract, which verifies attestations.

## Usage

These ABI files are used by the Web3.js or ethers.js libraries to interact with the smart contracts on the Flare blockchain. They define the interface for the contract functions, events, and state variables.

Example usage in JavaScript:

```javascript
const Web3 = require('web3');
const web3 = new Web3('https://coston2-api.flare.network/ext/C/rpc');

// Load ABI
const dataPurchaseAbi = require('./datapurchase_abi.json');

// Create contract instance
const dataPurchaseContract = new web3.eth.Contract(
  dataPurchaseAbi,
  '0xYourDeployedDataPurchaseAddress'
);

// Call contract function
dataPurchaseContract.methods.purchase(requestId)
  .send({ from: account, value: web3.utils.toWei('0.1', 'ether') })
  .then(receipt => {
    console.log('Transaction receipt:', receipt);
  });
```

Example usage in Python:

```python
import json
from web3 import Web3

# Connect to Flare network
w3 = Web3(Web3.HTTPProvider('https://coston2-api.flare.network/ext/C/rpc'))

# Load ABI
with open('./abi/datapurchase_abi.json') as f:
    datapurchase_abi = json.load(f)

# Create contract instance
contract = w3.eth.contract(address='0xYourDeployedDataPurchaseAddress', abi=datapurchase_abi)

# Call contract function
tx = contract.functions.purchase(request_id).build_transaction({
    'from': account.address,
    'value': w3.toWei('0.1', 'ether'),
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 2000000,
    'gasPrice': w3.eth.gas_price
})
