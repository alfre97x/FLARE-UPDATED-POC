"""
Flare Data Connector (FDC) Integration
Implements proper FDC workflow according to Flare documentation
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# FDC Configuration
RPC_URL = os.getenv('RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
# Different verifier hosts for different attestation types
EVM_VERIFIER_API = os.getenv('EVM_VERIFIER_API', 'https://fdc-verifiers-testnet.flare.network')
JSONAPI_VERIFIER_API = os.getenv('JSONAPI_VERIFIER_API', 'https://jq-verifier-test.flare.rocks')
DA_LAYER_API = os.getenv('DA_LAYER_API', 'https://ctn2-data-availability.flare.network')
FLARE_CONTRACT_REGISTRY = os.getenv('FLARE_CONTRACT_REGISTRY', '0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019')
FDC_API_KEY = os.getenv('FDC_API_KEY', '00000000-0000-0000-0000-000000000000')

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load ABIs
def load_abi(file_path: str) -> list:
    """Load ABI from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading ABI from {file_path}: {e}")
        return []

# Load all required ABIs
FDC_HUB_ABI = load_abi('abi/fdc_hub_abi.json')
REGISTRY_ABI = load_abi('abi/flare_contract_registry_abi.json')
FEE_CONFIG_ABI = load_abi('abi/fdc_request_fee_configurations_abi.json')

# Initialize account from private key
account = None
if PRIVATE_KEY:
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        logger.info(f"Initialized FDC account: {account.address}")
    except Exception as e:
        logger.error(f"Error initializing account: {e}")


def pad32(s: str) -> str:
    """Convert string to 32-byte hex padded format"""
    return "0x" + s.encode().hex().ljust(64, "0")


class FDCIntegration:
    """Flare Data Connector Integration Service"""
    
    def __init__(self):
        self.registry_contract = None
        self.fdc_hub_contract = None
        self.fee_config_contract = None
        self._initialize_contracts()
    
    def _initialize_contracts(self):
        """Initialize contracts via Contract Registry"""
        try:
            # Initialize Contract Registry
            registry_address = w3.to_checksum_address(FLARE_CONTRACT_REGISTRY)
            self.registry_contract = w3.eth.contract(
                address=registry_address,
                abi=REGISTRY_ABI
            )
            
            logger.info(f"Initialized Contract Registry at {registry_address}")
            
            # Resolve FDC Hub address
            fdc_hub_address = self.registry_contract.functions.getContractAddressByName("FdcHub").call()
            self.fdc_hub_contract = w3.eth.contract(
                address=fdc_hub_address,
                abi=FDC_HUB_ABI
            )
            
            # Resolve Fee Configuration address
            fee_config_address = self.registry_contract.functions.getContractAddressByName("FdcRequestFeeConfigurations").call()
            self.fee_config_contract = w3.eth.contract(
                address=fee_config_address,
                abi=FEE_CONFIG_ABI
            )
            
            logger.info(f"Resolved FDC Hub: {fdc_hub_address}")
            logger.info(f"Resolved Fee Config: {fee_config_address}")
            
        except Exception as e:
            logger.error(f"Error initializing FDC contracts: {e}")
    
    def prepare_evm_transaction_request(self, tx_hash: str) -> Optional[bytes]:
        """
        Prepare EVMTransaction attestation request (for testing first)
        
        Args:
            tx_hash: Transaction hash to attest
            
        Returns:
            abiEncodedRequest bytes or None if failed
        """
        try:
            # Prepare request payload for EVMTransaction attestation
            request_payload = {
                "attestationType": pad32("EVMTransaction"),
                "sourceId": pad32("testETH"), 
                "requestBody": {
                    "transactionHash": tx_hash,
                    "requiredConfirmations": "1",
                    "provideInput": True,  # Boolean, not string
                    "listEvents": True,    # Boolean, not string
                    "logIndices": []       # Array, not string
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-KEY': FDC_API_KEY  # Correct header case!
            }
            
            # Use correct endpoint for EVMTransaction
            endpoint = f"{EVM_VERIFIER_API}/verifier/eth/EVMTransaction/prepareRequest"
            
            response = requests.post(endpoint, json=request_payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"EVM Verifier API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            abi_encoded_request = result.get('abiEncodedRequest')
            
            if not abi_encoded_request:
                logger.error("No abiEncodedRequest in verifier response")
                return None
            
            # Convert hex string to bytes
            if abi_encoded_request.startswith('0x'):
                abi_encoded_request = abi_encoded_request[2:]
            
            return bytes.fromhex(abi_encoded_request)
            
        except Exception as e:
            logger.error(f"Error preparing EVMTransaction request: {e}")
            return None

    def prepare_jsonapi_request(self, url: str, post_process_jq: str = "{temp: .main.temp, city: .name}", abi_signature: str = "tuple(uint256 temp,string city)") -> Optional[bytes]:
        """
        Prepare JsonApi (Web2Json) attestation request with correct format
        
        Args:
            url: URL to fetch and attest
            post_process_jq: JQ expression to extract and format data
            abi_signature: ABI signature matching the JQ output structure
            
        Returns:
            abiEncodedRequest bytes or None if failed
        """
        try:
            # Prepare request payload for JsonApi attestation
            request_payload = {
                "attestationType": pad32("JsonApi"),  # Correct attestation type
                "sourceId": pad32("WEB2"),  # Correct source ID for Web2Json
                "requestBody": {
                    "url": url,
                    "httpMethod": "GET",
                    "headers": "{}",  # stringified JSON
                    "queryParams": "{}",
                    "body": "{}",
                    "postProcessJq": post_process_jq,  # Required for JsonApi!
                    "abiSignature": abi_signature  # Required for JsonApi!
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-KEY': FDC_API_KEY  # Correct header case!
            }
            
            # Use correct JsonApi verifier host and endpoint
            # Need to check the exact endpoint from the Swagger UI
            endpoint = f"{JSONAPI_VERIFIER_API}/verifier/web/JsonApi/prepareRequest"
            
            response = requests.post(endpoint, json=request_payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"JsonApi Verifier API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            abi_encoded_request = result.get('abiEncodedRequest')
            
            if not abi_encoded_request:
                logger.error("No abiEncodedRequest in verifier response")
                return None
            
            # Convert hex string to bytes
            if abi_encoded_request.startswith('0x'):
                abi_encoded_request = abi_encoded_request[2:]
            
            return bytes.fromhex(abi_encoded_request)
            
        except Exception as e:
            logger.error(f"Error preparing JsonApi request: {e}")
            return None

    def get_request_fee(self, abi_encoded_request: bytes) -> int:
        """
        Get request fee for attestation
        
        Args:
            abi_encoded_request: The ABI encoded request
            
        Returns:
            Fee in wei
        """
        try:
            if not self.fee_config_contract:
                logger.error("Fee config contract not initialized")
                return 0
            
            fee = self.fee_config_contract.functions.getRequestFee(abi_encoded_request).call()
            logger.info(f"Request fee: {fee} wei ({fee / 10**18:.6f} FLR)")
            return fee
            
        except Exception as e:
            logger.error(f"Error getting request fee: {e}")
            return 0
    
    def request_attestation(self, abi_encoded_request: bytes) -> Dict[str, Any]:
        """
        Submit attestation request to FDC Hub
        
        Args:
            abi_encoded_request: ABI encoded request from verifier
            
        Returns:
            Dictionary with transaction result
        """
        try:
            if not self.fdc_hub_contract or not account:
                return {
                    "success": False,
                    "error": "FDC Hub contract or account not initialized"
                }
            
            # Get request fee
            request_fee = self.get_request_fee(abi_encoded_request)
            
            if request_fee == 0:
                return {
                    "success": False,
                    "error": "Could not determine request fee"
                }
            
            # Build payable transaction
            tx = self.fdc_hub_contract.functions.requestAttestation(abi_encoded_request).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'value': request_fee,  # Pay the fee!
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            raw_tx = getattr(signed_tx, 'rawTransaction', signed_tx.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            
            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Check if transaction succeeded
            if receipt.status == 0:
                logger.error(f"FDC transaction failed: {tx_hash.hex()}")
                return {
                    "success": False,
                    "error": "Transaction failed (reverted)",
                    "transactionHash": tx_hash.hex()
                }
            
            # Extract request ID from events
            request_id = None
            for log in receipt.logs:
                try:
                    event = self.fdc_hub_contract.events.AttestationRequested().process_log(log)
                    request_id = event.args.requestId.hex()
                    logger.info(f"Attestation requested with ID: {request_id}")
                    break
                except:
                    continue
            
            logger.info(f"Successfully submitted FDC request: {tx_hash.hex()}")
            
            return {
                "success": True,
                "transactionHash": tx_hash.hex(),
                "requestId": request_id,
                "fee": request_fee
            }
            
        except Exception as e:
            logger.error(f"Error requesting FDC attestation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def fetch_attestation_result(self, request_id: str) -> Dict[str, Any]:
        """
        Fetch attestation result from DA Layer
        
        Args:
            request_id: Request ID from attestation request
            
        Returns:
            Dictionary with attestation result
        """
        try:
            # Clean request ID
            clean_request_id = request_id[2:] if request_id.startswith('0x') else request_id
            
            # Fetch from DA Layer API
            url = f"{DA_LAYER_API}/api/v1/fdc/proof-by-request-round/{clean_request_id}"
            
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.error(f"DA Layer API error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"DA Layer API error: {response.status_code}"
                }
            
            result = response.json()
            
            logger.info(f"Successfully fetched attestation result for request: {request_id}")
            
            return {
                "success": True,
                "attestationResponse": result.get('attestationResponse'),
                "proof": result.get('proof'),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error fetching attestation result: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def attest_satellite_data(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attest satellite data using JsonApi attestation type
        
        Args:
            satellite_data: Dictionary containing satellite data
            
        Returns:
            Dictionary with attestation result
        """
        try:
            # Create a JQ expression to extract satellite data fields
            satellite_jq = f'{{id: .id, datetime: .datetime, cloud_cover: .cloud_cover}}'
            satellite_abi = "tuple(string id,string datetime,uint256 cloud_cover)"
            
            # For testing, we'll use httpbin.org with appropriate JQ
            test_url = "https://httpbin.org/json"  # Returns predictable JSON structure
            test_jq = "{slideshow_title: .slideshow.title, author: .slideshow.author}"
            test_abi = "tuple(string slideshow_title,string author)"
            
            logger.info(f"Preparing JsonApi attestation for satellite data")
            logger.info(f"Satellite data: {satellite_data}")
            
            # Prepare the JsonApi request
            abi_encoded_request = self.prepare_jsonapi_request(
                url=test_url,
                post_process_jq=test_jq,
                abi_signature=test_abi
            )
            
            if not abi_encoded_request:
                return {
                    "success": False,
                    "error": "Failed to prepare JsonApi request"
                }
            
            # Submit attestation request
            result = self.request_attestation(abi_encoded_request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error attesting satellite data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_contract_addresses(self) -> Dict[str, str]:
        """Get current contract addresses from registry"""
        try:
            if not self.registry_contract:
                return {}
            
            addresses = {
                "ContractRegistry": FLARE_CONTRACT_REGISTRY,
                "FdcHub": self.fdc_hub_contract.address if self.fdc_hub_contract else "Not resolved",
                "FdcRequestFeeConfigurations": self.fee_config_contract.address if self.fee_config_contract else "Not resolved"
            }
            
            return addresses
            
        except Exception as e:
            logger.error(f"Error getting contract addresses: {e}")
            return {}
