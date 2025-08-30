"""
Blockchain API for SpaceData application
Handles integration with Flare blockchain for data purchase and verification
"""

import os
import json
import logging
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a file handler to log to a file
file_handler = logging.FileHandler('blockchain_api.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Blockchain configuration
RPC_URL = os.getenv('RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
DATAPURCHASE_CONTRACT_ADDRESS = os.getenv('DATAPURCHASE_CONTRACT_ADDRESS')
FDC_HUB_ADDRESS = os.getenv('FDC_HUB_ADDRESS')
FDC_VERIFICATION_ADDRESS = os.getenv('FDC_VERIFICATION_ADDRESS')
DA_LAYER_API = os.getenv('DA_LAYER_API', 'https://api.da.coston2.flare.network')
FDC_REQUEST_FEE_WEI = int(os.getenv('FDC_REQUEST_FEE_WEI', '0'))

# Log the loaded configuration
logger.info(f"Loaded blockchain configuration:")
logger.info(f"RPC_URL: {RPC_URL}")
logger.info(f"DATAPURCHASE_CONTRACT_ADDRESS: {DATAPURCHASE_CONTRACT_ADDRESS}")
logger.info(f"FDC_HUB_ADDRESS: {FDC_HUB_ADDRESS}")
logger.info(f"FDC_VERIFICATION_ADDRESS: {FDC_VERIFICATION_ADDRESS}")
logger.info(f"DA_LAYER_API: {DA_LAYER_API}")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load contract ABIs
try:
    with open('python_backend/static/js/DataPurchaseABI.json') as f:
        datapurchase_abi = json.load(f)
    
    with open('python_backend/static/js/FdcHubABI.json') as f:
        fdc_hub_abi = json.load(f)
    
    with open('python_backend/static/js/FdcVerificationABI.json') as f:
        fdc_verification_abi = json.load(f)
    
    logger.info("Successfully loaded contract ABIs")
except Exception as e:
    logger.error(f"Error loading contract ABIs: {str(e)}")
    # Create empty ABIs as fallback
    datapurchase_abi = []
    fdc_hub_abi = []
    fdc_verification_abi = []

# Initialize account from private key if available
account = None
if PRIVATE_KEY:
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        logger.info(f"Initialized account: {account.address}")
    except Exception as e:
        logger.error(f"Error initializing account from private key: {str(e)}")

# Initialize contracts if addresses are available
datapurchase_contract = None
fdc_hub_contract = None
fdc_verification_contract = None

if DATAPURCHASE_CONTRACT_ADDRESS:
    try:
        # Convert address to checksum format
        checksum_address = w3.to_checksum_address(DATAPURCHASE_CONTRACT_ADDRESS)
        datapurchase_contract = w3.eth.contract(
            address=checksum_address,
            abi=datapurchase_abi
        )
        logger.info(f"Initialized DataPurchase contract at {checksum_address}")
    except Exception as e:
        logger.error(f"Error initializing DataPurchase contract: {str(e)}")

if FDC_HUB_ADDRESS:
    try:
        # Convert address to checksum format
        checksum_address = w3.to_checksum_address(FDC_HUB_ADDRESS)
        fdc_hub_contract = w3.eth.contract(
            address=checksum_address,
            abi=fdc_hub_abi
        )
        logger.info(f"Initialized FDC Hub contract at {checksum_address}")
    except Exception as e:
        logger.error(f"Error initializing FDC Hub contract: {str(e)}")

if FDC_VERIFICATION_ADDRESS:
    try:
        # Convert address to checksum format
        checksum_address = w3.to_checksum_address(FDC_VERIFICATION_ADDRESS)
        fdc_verification_contract = w3.eth.contract(
            address=checksum_address,
            abi=fdc_verification_abi
        )
        logger.info(f"Initialized FDC Verification contract at {checksum_address}")
    except Exception as e:
        logger.error(f"Error initializing FDC Verification contract: {str(e)}")


class BlockchainAPI:
    """Service for blockchain-related functionality"""
    
    @staticmethod
    def get_config() -> Dict[str, str]:
        """
        Get blockchain configuration for frontend
        
        Returns:
            Dictionary with blockchain configuration
        """
        return {
            "rpcUrl": RPC_URL,
            "dataPurchaseContractAddress": DATAPURCHASE_CONTRACT_ADDRESS,
            "fdcHubAddress": FDC_HUB_ADDRESS,
            "fdcVerificationAddress": FDC_VERIFICATION_ADDRESS,
            "daLayerApi": DA_LAYER_API
        }
    
    @staticmethod
    def request_attestation(attestation_type: str, parameters: str) -> Dict[str, Any]:
        """
        Request attestation from FDC Hub
        
        Args:
            attestation_type: Type of attestation (e.g., "satellite.observation")
            parameters: Parameters for attestation (e.g., metadata hash)
            
        Returns:
            Dictionary with transaction result
        """
        if not fdc_hub_contract or not account:
            logger.error("FDC Hub contract or account not initialized")
            return {
                "success": False,
                "error": "FDC Hub contract or account not initialized"
            }
        
        try:
            # Encode attestation_type and parameters into bytes as expected by contract
            # ABI encode the two string parameters as (string, string)
            encoded_request = w3.codec.encode(['string', 'string'], [attestation_type, parameters])
            
            # Build transaction with single encoded bytes parameter
            tx = fdc_hub_contract.functions.requestAttestation(
                encoded_request
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price,
                'value': FDC_REQUEST_FEE_WEI  # Add fee for FDC Hub service
            })
            
            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            # Handle both old and new Web3.py versions
            raw_tx = getattr(signed_tx, 'rawTransaction', signed_tx.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Check if transaction was successful
            if receipt.status == 0:
                logger.error(f"Transaction failed with hash: {tx_hash.hex()}")
                return {
                    "success": False,
                    "error": "Transaction failed (reverted)",
                    "transactionHash": tx_hash.hex()
                }
            
            # Get request ID from event logs
            request_id = None
            for log in receipt.logs:
                try:
                    # Try to decode the log
                    event = fdc_hub_contract.events.AttestationRequested().process_log(log)
                    request_id = event.args.requestId.hex()
                    break
                except:
                    # Not the event we're looking for
                    continue
            
            logger.info(f"Successfully requested attestation: {tx_hash.hex()}")
            
            return {
                "success": True,
                "transactionHash": tx_hash.hex(),
                "requestId": request_id
            }
        except Exception as e:
            logger.error(f"Error requesting attestation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def fetch_attestation_result(request_id: str) -> Dict[str, Any]:
        """
        Fetch attestation result from DA Layer API
        
        Args:
            request_id: Request ID
            
        Returns:
            Dictionary with attestation result
        """
        try:
            # Remove 0x prefix if present
            clean_request_id = request_id[2:] if request_id.startswith('0x') else request_id
            
            # Construct URL
            url = f"{DA_LAYER_API}/attestations/{clean_request_id}"
            
            # Fetch attestation result
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.error(f"Error fetching attestation result: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Error fetching attestation result: {response.status_code}"
                }
            
            result = response.json()
            
            logger.info(f"Successfully fetched attestation result for request ID: {request_id}")
            
            return {
                "success": True,
                "attestationResponse": result.get('attestationResponse'),
                "proof": result.get('proof')
            }
        except Exception as e:
            logger.error(f"Error fetching attestation result: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def verify_attestation(request_id: str, attestation_response: str, proof: str) -> Dict[str, Any]:
        """
        Verify attestation using FDC Verification contract
        
        Args:
            request_id: Request ID (must be 32 bytes hex)
            attestation_response: Attestation response (must be 32 bytes hex)
            proof: Proof (arbitrary length bytes hex)
            
        Returns:
            Dictionary with verification result
        """
        if not fdc_verification_contract:
            logger.error("FDC Verification contract not initialized")
            return {
                "success": False,
                "error": "FDC Verification contract not initialized"
            }
        
        try:
            # Validate and convert request_id to bytes32 (exactly 32 bytes)
            request_id_hex = request_id[2:] if request_id.startswith('0x') else request_id
            if len(request_id_hex) != 64:  # 32 bytes = 64 hex chars
                return {
                    "success": False,
                    "error": f"Invalid request_id: must be 32 bytes (64 hex chars), got {len(request_id_hex)}"
                }
            request_id_bytes = bytes.fromhex(request_id_hex)
            
            # Validate and convert attestation_response to bytes32 (exactly 32 bytes)
            attestation_response_hex = attestation_response[2:] if attestation_response.startswith('0x') else attestation_response
            if len(attestation_response_hex) != 64:  # 32 bytes = 64 hex chars
                return {
                    "success": False,
                    "error": f"Invalid attestation_response: must be 32 bytes (64 hex chars), got {len(attestation_response_hex)}"
                }
            attestation_response_bytes = bytes.fromhex(attestation_response_hex)
            
            # Convert proof to bytes (arbitrary length)
            proof_hex = proof[2:] if proof.startswith('0x') else proof
            proof_bytes = bytes.fromhex(proof_hex)
            
            # Call the verifyAttestation function
            is_valid = fdc_verification_contract.functions.verifyAttestation(
                request_id_bytes,
                attestation_response_bytes,
                proof_bytes
            ).call()
            
            logger.info(f"Attestation verification result for request ID {request_id}: {is_valid}")
            
            return {
                "success": True,
                "verified": is_valid
            }
        except Exception as e:
            logger.error(f"Error verifying attestation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def deliver_data(request_id: str, attestation_response: str, proof: str) -> Dict[str, Any]:
        """
        Deliver data to DataPurchase contract
        
        Args:
            request_id: Request ID (must be 32 bytes hex)
            attestation_response: Attestation response (must be 32 bytes hex)
            proof: Proof (arbitrary length bytes hex)
            
        Returns:
            Dictionary with transaction result
        """
        if not datapurchase_contract or not account:
            logger.error("DataPurchase contract or account not initialized")
            return {
                "success": False,
                "error": "DataPurchase contract or account not initialized"
            }
        
        try:
            # Validate and convert request_id to bytes32 (exactly 32 bytes)
            request_id_hex = request_id[2:] if request_id.startswith('0x') else request_id
            if len(request_id_hex) != 64:  # 32 bytes = 64 hex chars
                return {
                    "success": False,
                    "error": f"Invalid request_id: must be 32 bytes (64 hex chars), got {len(request_id_hex)}"
                }
            request_id_bytes = bytes.fromhex(request_id_hex)
            
            # Validate and convert attestation_response to bytes32 (exactly 32 bytes)
            attestation_response_hex = attestation_response[2:] if attestation_response.startswith('0x') else attestation_response
            if len(attestation_response_hex) != 64:  # 32 bytes = 64 hex chars
                return {
                    "success": False,
                    "error": f"Invalid attestation_response: must be 32 bytes (64 hex chars), got {len(attestation_response_hex)}"
                }
            attestation_response_bytes = bytes.fromhex(attestation_response_hex)
            
            # Convert proof to bytes (arbitrary length)
            proof_hex = proof[2:] if proof.startswith('0x') else proof
            proof_bytes = bytes.fromhex(proof_hex)
            
            # Build transaction
            tx = datapurchase_contract.functions.deliverData(
                request_id_bytes,
                attestation_response_bytes,
                proof_bytes
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price
            })
            
            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            
            # Send transaction
            # Handle both old and new Web3.py versions
            raw_tx = getattr(signed_tx, 'rawTransaction', signed_tx.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Successfully delivered data: {tx_hash.hex()}")
            
            return {
                "success": True,
                "transactionHash": tx_hash.hex()
            }
        except Exception as e:
            logger.error(f"Error delivering data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def generate_request_id(data_info: Dict[str, Any]) -> str:
        """
        Generate a request ID for a data request
        
        Args:
            data_info: Dictionary with data information
            
        Returns:
            Request ID as a hex string
        """
        try:
            # Create a string representation of the data info
            data_str = json.dumps(data_info, sort_keys=True)
            
            # Generate a keccak256 hash
            request_id = w3.keccak(text=data_str).hex()
            
            logger.info(f"Generated request ID: {request_id}")
            
            return request_id
        except Exception as e:
            logger.error(f"Error generating request ID: {str(e)}")
            return w3.keccak(text=str(time.time())).hex()  # Fallback
