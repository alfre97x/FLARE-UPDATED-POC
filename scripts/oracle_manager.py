import os, time, requests, json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))

with open("./abi/datapurchase_abi.json") as f:
    datapurchase_abi = json.load(f)

contract = w3.eth.contract(address=os.getenv("DATAPURCHASE_CONTRACT_ADDRESS"), abi=datapurchase_abi)


def fetch_attestation_result(request_id):
    url = f"{os.getenv('DA_LAYER_API')}/attestations/{request_id.hex()}"
    response = requests.get(url)
    res = response.json()
    return bytes.fromhex(res['attestationResponse'][2:]), bytes.fromhex(res['proof'][2:])


def deliver(request_id, attestation_response, proof):
    tx = contract.functions.deliverData(request_id, attestation_response, proof).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, os.getenv("PRIVATE_KEY"))
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"✅ Delivered data: {tx_hash.hex()}")

# Example use
request_id = Web3.keccak(text="copernicus-job-123")  # Replace dynamically
print(f"🛰️ Simulating wait for requestId: {request_id.hex()}")
time.sleep(180)
response, proof = fetch_attestation_result(request_id)
deliver(request_id, response, proof)
