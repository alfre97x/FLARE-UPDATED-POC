#!/usr/bin/env python3
"""
Test script for DataPurchase contract
This script tests the basic functionality of the DataPurchase contract
"""

import os
import json
import sys
import time
from pathlib import Path
from web3 import Web3
# Try to import geth_poa_middleware, but handle the case where it's not available
try:
    from web3.middleware import geth_poa_middleware
    HAS_POA_MIDDLEWARE = True
except ImportError:
    print("Warning: geth_poa_middleware not available in this version of web3.py")
    print("If you're connecting to a POA chain like Flare, some features might not work correctly.")
    HAS_POA_MIDDLEWARE = False

from eth_account import Account
from dotenv import load_dotenv
from hexbytes import HexBytes

# Get the absolute path to the root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the root directory
DOTENV_PATH = ROOT_DIR / '.env'
load_dotenv(DOTENV_PATH)

# Verify RPC_URL is loaded
RPC_URL = os.getenv("RPC_URL")
if not RPC_URL:
    print("ERROR: RPC_URL not found in environment variables")
    print(f"Make sure the .env file exists at {DOTENV_PATH} and contains RPC_URL")
    sys.exit(1)
print(f"Connecting to RPC URL: {RPC_URL}")

# Load contract ABIs with absolute paths
DATAPURCHASE_ABI_PATH = ROOT_DIR / 'abi' / 'datapurchase_abi.json'
FDC_VERIFICATION_ABI_PATH = ROOT_DIR / 'abi' / 'fdc_verification_abi.json'

with open(DATAPURCHASE_ABI_PATH) as f:
    datapurchase_abi = json.load(f)

with open(FDC_VERIFICATION_ABI_PATH) as f:
    fdc_verification_abi = json.load(f)

# Connect to Flare Coston2 testnet
w3 = Web3(Web3.HTTPProvider(RPC_URL))
# Add POA middleware for Flare network if available
if HAS_POA_MIDDLEWARE:
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Set up account from private key
private_key = os.getenv("PRIVATE_KEY")
if private_key.startswith('0x'):
    account = Account.from_key(private_key)
else:
    account = Account.from_key(f"0x{private_key}")
from_address = account.address

# Contract addresses from .env - convert to checksum addresses
datapurchase_address = os.getenv("DATAPURCHASE_CONTRACT_ADDRESS")
fdc_verification_address = os.getenv("FDC_VERIFICATION_ADDRESS")

# Convert addresses to checksum format
if datapurchase_address:
    datapurchase_address = Web3.to_checksum_address(datapurchase_address)
if fdc_verification_address:
    fdc_verification_address = Web3.to_checksum_address(fdc_verification_address)

print(f"Using checksum addresses:")
print(f"DataPurchase: {datapurchase_address}")
print(f"FDC Verification: {fdc_verification_address}")

# Create contract instances
datapurchase_contract = w3.eth.contract(address=datapurchase_address, abi=datapurchase_abi)
fdc_verification_contract = w3.eth.contract(address=fdc_verification_address, abi=fdc_verification_abi)


def test_contract_deployment():
    """Test if the contract is deployed correctly"""
    print("\n--- Testing Contract Deployment ---")
    
    try:
        # Check if the contract exists by calling a view function
        owner = datapurchase_contract.functions.owner().call()
        print(f"✅ Contract deployed at {datapurchase_address}")
        print(f"✅ Contract owner: {owner}")
        
        # Check if the FDC verifier is set correctly
        fdc_verifier = datapurchase_contract.functions.fdcVerifier().call()
        print(f"✅ FDC Verifier set to: {fdc_verifier}")
        print(f"✅ Expected FDC Verifier: {fdc_verification_address}")
        
        if fdc_verifier.lower() != fdc_verification_address.lower():
            print("⚠️ FDC Verifier address does not match the one in .env file")
        
        return True
    except Exception as e:
        print(f"❌ Contract deployment test failed: {str(e)}")
        return False


def test_purchase_function():
    """Test the purchase function of the contract"""
    print("\n--- Testing Purchase Function ---")
    
    try:
        # Generate a test request ID
        request_id = w3.keccak(text=f"test-request-{int(time.time())}")
        print(f"📝 Test Request ID: {request_id.hex()}")
        
        # Check account balance
        balance = w3.eth.get_balance(from_address)
        print(f"💰 Account balance: {w3.from_wei(balance, 'ether')} FLR")
        
        # Set up purchase transaction
        payment_amount = w3.to_wei(0.01, 'ether')  # 0.01 FLR
        print(f"💸 Payment amount: {w3.from_wei(payment_amount, 'ether')} FLR")
        
        # Estimate gas for the transaction
        gas_estimate = datapurchase_contract.functions.purchase(request_id).estimate_gas({
            'from': from_address,
            'value': payment_amount
        })
        print(f"⛽ Estimated gas: {gas_estimate}")
        
        # Calculate gas with buffer (20%)
        gas_with_buffer = int(gas_estimate * 1.2)
        print(f"⛽ Gas with buffer: {gas_with_buffer}")
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(from_address)
        tx = datapurchase_contract.functions.purchase(request_id).build_transaction({
            'from': from_address,
            'value': payment_amount,
            'gas': gas_with_buffer,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce
        })
        
        # Sign and send transaction
        print("🔄 Sending purchase transaction...")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Transaction successful! Hash: {receipt['transactionHash'].hex()}")
        
        # Check for DataRequested event
        data_requested_event = datapurchase_contract.events.DataRequested().process_receipt(receipt)
        if data_requested_event:
            event = data_requested_event[0]
            print("✅ DataRequested event emitted")
            print(f"✅ Event buyer: {event['args']['buyer']}")
            print(f"✅ Event requestId: {event['args']['requestId'].hex()}")
        else:
            print("⚠️ DataRequested event not found in transaction receipt")
        
        # Check if request was stored in contract
        request = datapurchase_contract.functions.requests(request_id).call()
        print(f"✅ Request stored in contract: buyer={request[0]}, delivered={request[1]}")
        
        return {
            'success': True,
            'requestId': request_id
        }
    except Exception as e:
        print(f"❌ Purchase function test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def test_deliver_data_function(request_id):
    """Test the deliverData function of the contract"""
    print("\n--- Testing DeliverData Function ---")
    
    if not request_id:
        print("❌ No requestId provided for testing deliverData")
        return False
    
    if isinstance(request_id, dict) and 'requestId' in request_id:
        request_id = request_id['requestId']
    
    print(f"📝 Using Request ID: {request_id.hex() if isinstance(request_id, HexBytes) else request_id}")
    
    try:
        # In a real scenario, we would get these from the FDC system
        # For testing, we'll use mock values
        attestation_response = w3.keccak(text=f"mock-attestation-{int(time.time())}")
        mock_proof = bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
        
        print(f"📝 Mock Attestation Response: {attestation_response.hex()}")
        print(f"📝 Mock Proof Length: {len(mock_proof)} bytes")
        
        # Note: This will likely fail in a real test because the mock proof won't be valid
        # We would need a real attestation and proof from the FDC system
        print("⚠️ This test will likely fail because we are using mock data")
        print("⚠️ In a real scenario, we would need a valid attestation and proof from the FDC system")
        
        # Try to deliver data
        print("🔄 Attempting to deliver data...")
        
        try:
            # Estimate gas for the transaction
            gas_estimate = datapurchase_contract.functions.deliverData(
                request_id,
                attestation_response,
                mock_proof
            ).estimate_gas({
                'from': from_address
            })
            print(f"⛽ Estimated gas: {gas_estimate}")
            
            # Calculate gas with buffer (20%)
            gas_with_buffer = int(gas_estimate * 1.2)
            print(f"⛽ Gas with buffer: {gas_with_buffer}")
            
            # Build transaction
            nonce = w3.eth.get_transaction_count(from_address)
            tx = datapurchase_contract.functions.deliverData(
                request_id,
                attestation_response,
                mock_proof
            ).build_transaction({
                'from': from_address,
                'gas': gas_with_buffer,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Transaction successful! Hash: {receipt['transactionHash'].hex()}")
            
            # Check for DataDelivered event
            data_delivered_event = datapurchase_contract.events.DataDelivered().process_receipt(receipt)
            if data_delivered_event:
                event = data_delivered_event[0]
                print("✅ DataDelivered event emitted")
                print(f"✅ Event requestId: {event['args']['requestId'].hex()}")
                print(f"✅ Event dataHash: {event['args']['dataHash'].hex()}")
            else:
                print("⚠️ DataDelivered event not found in transaction receipt")
            
            # Check if request was marked as delivered
            request = datapurchase_contract.functions.requests(request_id).call()
            print(f"✅ Request updated in contract: buyer={request[0]}, delivered={request[1]}")
            
            return True
        except Exception as e:
            print(f"❌ DeliverData transaction failed: {str(e)}")
            print("ℹ️ This is expected if using mock data. In a real scenario, we would need valid attestation and proof.")
            
            # Check if we can verify the attestation directly
            try:
                print("🔄 Trying to verify attestation directly...")
                is_valid = fdc_verification_contract.functions.verifyAttestation(
                    request_id,
                    attestation_response,
                    mock_proof
                ).call()
                print(f"ℹ️ Direct verification result: {is_valid}")
            except Exception as verify_error:
                print(f"❌ Direct verification failed: {str(verify_error)}")
            
            return False
    except Exception as e:
        print(f"❌ DeliverData function test failed: {str(e)}")
        return False


def run_tests():
    """Main test function"""
    print("=== DataPurchase Contract Test ===")
    print(f"🔗 Connected to: {RPC_URL}")
    print(f"📝 Testing contract at: {datapurchase_address}")
    print(f"👤 Using account: {from_address}")
    
    # Test contract deployment
    deployment_ok = test_contract_deployment()
    if not deployment_ok:
        print("❌ Deployment test failed. Stopping tests.")
        return
    
    # Test purchase function
    purchase_result = test_purchase_function()
    if not purchase_result['success']:
        print("❌ Purchase test failed. Stopping tests.")
        return
    
    # Test deliverData function
    test_deliver_data_function(purchase_result['requestId'])
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    run_tests()
