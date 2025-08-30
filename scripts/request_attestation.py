import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))

with open("./abi/fdc_hub_abi.json") as f:
    fdc_hub_abi = json.load(f)

fdc_hub = w3.eth.contract(
    address=os.getenv("FDC_HUB_ADDRESS"), abi=fdc_hub_abi
)

attestation_type = "satellite.observation"
parameters = "Copernicus-L2A-Hash"

tx = fdc_hub.functions.requestAttestation(attestation_type, parameters).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 2000000,
    'gasPrice': w3.eth.gas_price
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=os.getenv("PRIVATE_KEY"))
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

print(f"✅ Attestation requested: {tx_hash.hex()}")
