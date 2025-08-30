#!/usr/bin/env python3
"""
FDC Hub Status Testing Script
Tests the current status of Flare Data Contract (FDC) Hub and related blockchain components
"""

import os
import sys
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configuration
RPC_URL = os.getenv('RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
FDC_HUB_ADDRESS = os.getenv('FDC_HUB_ADDRESS', '0x48aC463d797582898331F4De43341627b9c5f1D')
FDC_VERIFICATION_ADDRESS = os.getenv('FDC_VERIFICATION_ADDRESS', '0x075bf3f01fF07C4920e5261F9a366969640F5348')
DA_LAYER_API = os.getenv('DA_LAYER_API', 'https://api.da.coston2.flare.network')

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_test_result(test_name, success, details=""):
    """Print test result with consistent formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def test_blockchain_connectivity():
    """Test basic blockchain connectivity"""
    print_header("BLOCKCHAIN CONNECTIVITY TEST")
    
    try:
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        # Test connection
        if not w3.is_connected():
            print_test_result("Blockchain Connection", False, f"Cannot connect to {RPC_URL}")
            return False
        
        print_test_result("Blockchain Connection", True, f"Connected to {RPC_URL}")
        
        # Get network info
        try:
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number
            print_test_result("Network Info", True, f"Chain ID: {chain_id}, Latest Block: {block_number}")
        except Exception as e:
            print_test_result("Network Info", False, f"Error: {str(e)}")
            return False
        
        # Test account if private key is available
        if PRIVATE_KEY:
            try:
                account = w3.eth.account.from_key(PRIVATE_KEY)
                balance = w3.eth.get_balance(account.address)
                balance_eth = w3.from_wei(balance, 'ether')
                print_test_result("Account Info", True, f"Address: {account.address}, Balance: {balance_eth:.4f} FLR")
            except Exception as e:
                print_test_result("Account Info", False, f"Error: {str(e)}")
                return False
        else:
            print_test_result("Account Info", False, "No private key provided in .env file")
        
        return True
        
    except Exception as e:
        print_test_result("Blockchain Connection", False, f"Error: {str(e)}")
        return False

def test_fdc_hub_contract():
    """Test FDC Hub contract existence and basic functionality"""
    print_header("FDC HUB CONTRACT TEST")
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        if not w3.is_connected():
            print_test_result("FDC Hub Test", False, "No blockchain connection")
            return False
        
        # Check if contract exists at the address
        checksum_address = w3.to_checksum_address(FDC_HUB_ADDRESS)
        code = w3.eth.get_code(checksum_address)
        
        if len(code) == 0:
            print_test_result("FDC Hub Contract Exists", False, f"No contract code at {FDC_HUB_ADDRESS}")
            return False
        
        print_test_result("FDC Hub Contract Exists", True, f"Contract found at {checksum_address}")
        
        # Load ABI and test contract interaction
        try:
            with open('abi/fdc_hub_abi.json', 'r') as f:
                fdc_hub_abi = json.load(f)
            
            contract = w3.eth.contract(address=checksum_address, abi=fdc_hub_abi)
            print_test_result("FDC Hub ABI Loaded", True, f"ABI loaded with {len(fdc_hub_abi)} functions")
            
            # Test a read-only method if available (common ones)
            try:
                # Try to call common view functions
                view_functions = ['owner', 'name', 'version', 'getRequestInfo']
                function_called = None
                
                for func_name in view_functions:
                    if hasattr(contract.functions, func_name):
                        try:
                            result = getattr(contract.functions, func_name)().call()
                            print_test_result("FDC Hub Read Function", True, f"{func_name}() returned: {result}")
                            function_called = func_name
                            break
                        except Exception as e:
                            continue
                
                if not function_called:
                    print_test_result("FDC Hub Read Function", False, "No callable view functions found")
                    
            except Exception as e:
                print_test_result("FDC Hub Read Function", False, f"Error calling view functions: {str(e)}")
            
            return True
            
        except Exception as e:
            print_test_result("FDC Hub ABI", False, f"Error loading ABI: {str(e)}")
            return False
        
    except Exception as e:
        print_test_result("FDC Hub Test", False, f"Error: {str(e)}")
        return False

def test_fdc_verification_contract():
    """Test FDC Verification contract"""
    print_header("FDC VERIFICATION CONTRACT TEST")
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        if not w3.is_connected():
            print_test_result("FDC Verification Test", False, "No blockchain connection")
            return False
        
        # Check if contract exists at the address
        checksum_address = w3.to_checksum_address(FDC_VERIFICATION_ADDRESS)
        code = w3.eth.get_code(checksum_address)
        
        if len(code) == 0:
            print_test_result("FDC Verification Contract Exists", False, f"No contract code at {FDC_VERIFICATION_ADDRESS}")
            return False
        
        print_test_result("FDC Verification Contract Exists", True, f"Contract found at {checksum_address}")
        
        # Load ABI
        try:
            with open('abi/fdc_verification_abi.json', 'r') as f:
                fdc_verification_abi = json.load(f)
            
            contract = w3.eth.contract(address=checksum_address, abi=fdc_verification_abi)
            print_test_result("FDC Verification ABI Loaded", True, f"ABI loaded with {len(fdc_verification_abi)} functions")
            return True
            
        except Exception as e:
            print_test_result("FDC Verification ABI", False, f"Error loading ABI: {str(e)}")
            return False
        
    except Exception as e:
        print_test_result("FDC Verification Test", False, f"Error: {str(e)}")
        return False

def test_da_layer_api():
    """Test DA Layer API connectivity"""
    print_header("DA LAYER API TEST")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{DA_LAYER_API}/health", timeout=10)
        if response.status_code == 200:
            print_test_result("DA Layer API Health", True, f"API responded with status {response.status_code}")
        else:
            print_test_result("DA Layer API Health", False, f"API responded with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print_test_result("DA Layer API Health", False, f"Connection error: {str(e)}")
    
    # Test attestations endpoint
    try:
        # Try to get attestations (might return 404 or empty, but should not error)
        response = requests.get(f"{DA_LAYER_API}/attestations", timeout=10)
        print_test_result("DA Layer Attestations Endpoint", True, f"Endpoint accessible, status: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print_test_result("DA Layer Attestations Endpoint", False, f"Connection error: {str(e)}")

def test_attestation_flow():
    """Test a complete attestation request flow"""
    print_header("ATTESTATION FLOW TEST")
    
    if not PRIVATE_KEY:
        print_test_result("Attestation Flow", False, "No private key provided - cannot test transactions")
        return False
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        account = w3.eth.account.from_key(PRIVATE_KEY)
        
        # Load contracts
        with open('abi/fdc_hub_abi.json', 'r') as f:
            fdc_hub_abi = json.load(f)
        
        fdc_hub_contract = w3.eth.contract(
            address=w3.to_checksum_address(FDC_HUB_ADDRESS),
            abi=fdc_hub_abi
        )
        
        # Test parameters
        attestation_type = "satellite.observation.test"
        parameters = f"test-{int(time.time())}"
        
        print(f"Testing attestation request...")
        print(f"  Type: {attestation_type}")
        print(f"  Parameters: {parameters}")
        print(f"  From: {account.address}")
        
        # Check balance first
        balance = w3.eth.get_balance(account.address)
        if balance == 0:
            print_test_result("Attestation Flow", False, "Account has zero balance - cannot pay for gas")
            return False
        
        # Build transaction
        try:
            # Encode attestation_type and parameters into bytes as expected by contract
            # ABI encode the two string parameters as (string, string)
            encoded_request = w3.codec.encode(['string', 'string'], [attestation_type, parameters])
            
            tx = fdc_hub_contract.functions.requestAttestation(
                encoded_request
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price,
                'value': int(os.getenv('FDC_REQUEST_FEE_WEI', '0'))  # Add optional fee
            })
            
            print_test_result("Transaction Build", True, f"Gas price: {w3.eth.gas_price}, Nonce: {tx['nonce']}")
            
        except Exception as e:
            print_test_result("Transaction Build", False, f"Error building transaction: {str(e)}")
            return False
        
        # Sign transaction
        try:
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            print_test_result("Transaction Signing", True, "Transaction signed successfully")
        except Exception as e:
            print_test_result("Transaction Signing", False, f"Error signing transaction: {str(e)}")
            return False
        
        # Send transaction
        try:
            print("Sending transaction to blockchain...")
            # Handle both old and new Web3.py versions
            raw_tx = getattr(signed_tx, 'rawTransaction', signed_tx.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            print_test_result("Transaction Send", True, f"Transaction hash: {tx_hash.hex()}")
            
            # Wait for receipt
            print("Waiting for transaction receipt...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                print_test_result("Transaction Receipt", True, f"Transaction mined in block {receipt.blockNumber}")
                
                # Try to get request ID from logs
                request_id = None
                for log in receipt.logs:
                    try:
                        # Try to decode AttestationRequested event
                        event = fdc_hub_contract.events.AttestationRequested().process_log(log)
                        request_id = event.args.requestId.hex()
                        print_test_result("Attestation Request ID", True, f"Request ID: {request_id}")
                        break
                    except:
                        continue
                
                if not request_id:
                    print_test_result("Attestation Request ID", False, "Could not extract request ID from logs")
                
                return True
            else:
                print_test_result("Transaction Receipt", False, f"Transaction failed - status: {receipt.status}")
                return False
                
        except Exception as e:
            print_test_result("Transaction Send", False, f"Error sending transaction: {str(e)}")
            return False
        
    except Exception as e:
        print_test_result("Attestation Flow", False, f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🔍 FDC Hub Status Testing Script")
    print("Testing Flare Data Contract Hub and blockchain integration...")
    
    # Check environment variables
    print_header("ENVIRONMENT CONFIGURATION")
    print(f"RPC_URL: {RPC_URL}")
    print(f"FDC_HUB_ADDRESS: {FDC_HUB_ADDRESS}")
    print(f"FDC_VERIFICATION_ADDRESS: {FDC_VERIFICATION_ADDRESS}")
    print(f"DA_LAYER_API: {DA_LAYER_API}")
    print(f"PRIVATE_KEY: {'✅ Set' if PRIVATE_KEY else '❌ Not Set'}")
    
    # Run tests
    tests = [
        ("Blockchain Connectivity", test_blockchain_connectivity),
        ("FDC Hub Contract", test_fdc_hub_contract),
        ("FDC Verification Contract", test_fdc_verification_contract),
        ("DA Layer API", test_da_layer_api),
        ("Attestation Flow", test_attestation_flow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_test_result(test_name, False, f"Unexpected error: {str(e)}")
            results[test_name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FDC Hub integration appears to be working.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        
        # Provide recommendations
        if not results.get("Blockchain Connectivity", False):
            print("\n💡 Recommendations:")
            print("   - Check your RPC_URL in the .env file")
            print("   - Verify internet connection")
            print("   - Try a different Flare RPC endpoint")
        
        if not results.get("FDC Hub Contract", False):
            print("\n💡 FDC Hub Issues:")
            print("   - Contract address may have changed")
            print("   - Contract may not be deployed on this network")
            print("   - Check with Flare team for current addresses")
        
        if not results.get("Attestation Flow", False):
            print("\n💡 Attestation Issues:")
            print("   - Make sure you have FLR balance for gas fees")
            print("   - Verify private key is correct")
            print("   - Check if FDC Hub is accepting requests")

if __name__ == "__main__":
    main()
