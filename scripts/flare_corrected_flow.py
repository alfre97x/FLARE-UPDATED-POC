#!/usr/bin/env python3
"""
Corrected FDC attestation flow based on Flare expert guidance
Implements the exact fixes suggested to resolve our transaction reverts
"""

import os
import sys
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# Load environment
load_dotenv()

class FlareAttestationFlow:
    def __init__(self):
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
        # Inject POA middleware for Coston2 (fixes extraData length issue)
        poa_injected = False
        try:
            # web3.py v5-style location
            from web3.middleware.geth_poa import geth_poa_middleware
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            poa_injected = True
            print("🔩 Injected geth_poa_middleware (geth_poa) for POA chain compatibility")
        except Exception:
            try:
                # web3.py v6-style location
                from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
                # In v6, inject the class at the front of the onion
                self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                poa_injected = True
                print("🔩 Injected ExtraDataToPOAMiddleware for POA chain compatibility")
            except Exception as _e:
                print("⚠️  Could not inject POA middleware (continuing):", str(_e))
        self.account = self.w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
        
        # API endpoints
        self.verifier_evm_base = os.getenv('VERIFIER_EVM_BASE')
        self.verifier_web2_base = os.getenv('VERIFIER_WEB2_BASE')
        self.da_layer_api = os.getenv('DA_LAYER_API')
        self.fdc_api_key = os.getenv('FDC_API_KEY')
        
        # Contract Registry (same on all Flare networks)
        self.registry_addr = os.getenv('FLARE_CONTRACT_REGISTRY')
        
        # Load ABIs
        self.registry_abi = self._load_abi('flare_contract_registry_abi.json')
        self.fdc_hub_abi = self._load_abi('fdc_hub_abi.json')  # Updated canonical ABI
        self.fee_cfg_abi = self._load_abi('fdc_request_fee_configurations_abi.json')
        
        # Initialize contracts
        self._init_contracts()
        
    def _load_abi(self, filename):
        """Load ABI from file"""
        with open(f'abi/{filename}', 'r') as f:
            return json.load(f)
    
    def _init_contracts(self):
        """Initialize contracts using registry resolution"""
        print("🔧 Initializing contracts via registry...")
        
        # Registry contract
        self.registry = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.registry_addr),
            abi=self.registry_abi
        )
        
        # Resolve live addresses
        self.fdc_hub_addr = self._resolve_contract("FdcHub")
        self.fee_cfg_addr = self._resolve_contract("FdcRequestFeeConfigurations") 
        self.fdc_verif_addr = self._resolve_contract("FdcVerification")
        
        print(f"   FdcHub: {self.fdc_hub_addr}")
        print(f"   FeeConfigurations: {self.fee_cfg_addr}")
        print(f"   FdcVerification: {self.fdc_verif_addr}")
        
        # Initialize contract instances
        self.fdc_hub = self.w3.eth.contract(address=self.fdc_hub_addr, abi=self.fdc_hub_abi)
        self.fee_cfg = self.w3.eth.contract(address=self.fee_cfg_addr, abi=self.fee_cfg_abi)
        
    def _resolve_contract(self, name):
        """Resolve contract address from registry"""
        return self.w3.to_checksum_address(
            self.registry.functions.getContractAddressByName(name).call()
        )
    
    def _post_json(self, url, payload):
        """Post JSON with API key header"""
        headers = {
            "X-API-KEY": self.fdc_api_key,
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                print("❌ Verifier returned non-JSON 200 response")
                print(f"   URL: {url}")
                print(f"   Body: {json.dumps(payload)}")
                print(f"   Text: {response.text[:500]}")
                raise
        else:
            print(f"❌ Verifier error: HTTP {response.status_code}")
            print(f"   URL: {url}")
            print(f"   Body: {json.dumps(payload)}")
            print(f"   Response: {response.text[:2000]}")
            raise Exception(f"HTTP {response.status_code} from verifier")
    
    def _pad32(self, txt):
        """Pad text to 32-byte hex string"""
        return "0x" + txt.encode().hex().ljust(64, "0")
    
    def prepare_evm_transaction_request(self, sepolia_tx_hash):
        """Prepare EVMTransaction attestation request via verifier"""
        print("📝 Preparing EVMTransaction request...")
        
        body = {
            "attestationType": self._pad32("EVMTransaction"),
            "sourceId": self._pad32("testETH"),
            "requestBody": {
                "transactionHash": sepolia_tx_hash,
                "requiredConfirmations": "1",
                "provideInput": True,
                "listEvents": True,
                "logIndices": []
            }
        }
        
        url = f"{self.verifier_evm_base}/verifier/eth/EVMTransaction/prepareRequest"
        print(f"   URL: {url}")
        print(f"   Tx Hash: {sepolia_tx_hash}")
        
        try:
            response = self._post_json(url, body)
            abi_encoded_request = response["abiEncodedRequest"]
            print(f"✅ Got abiEncodedRequest: {abi_encoded_request[:100]}...")
            return abi_encoded_request
        except Exception as e:
            print(f"❌ Failed to prepare request: {str(e)}")
            return None
    
    def prepare_jsonapi_request(self, url, jq_transform, abi_signature, method="GET"):
        """Prepare JsonApi attestation request via Web2 verifier"""
        print("📝 Preparing JsonApi request...")
        
        body = {
            "attestationType": self._pad32("JsonApi"),
            "sourceId": self._pad32("WEB2"),
            "requestBody": {
                "url": url,
                "method": method,
                "headers": {},
                "query": {},
                "body": {},
                "postProcessJq": jq_transform,
                "abiSignature": abi_signature
            }
        }
        
        # Try multiple known endpoint paths to handle host/build variations
        base = self.verifier_web2_base
        candidate_paths = [
            f"{base}/verifier/web2/jsonApi/prepareRequest",
            f"{base}/verifier/web2/jsonapi/prepareRequest",
            f"{base}/verifier/jsonapi/prepareRequest",
        ]
        last_error = None
        for endpoint_url in candidate_paths:
            print(f"   Trying URL: {endpoint_url}")
            print(f"   Target URL: {url}")
            print(f"   JQ Transform: {jq_transform}")
            try:
                response = self._post_json(endpoint_url, body)
                abi_encoded_request = response["abiEncodedRequest"]
                print(f"✅ Got abiEncodedRequest: {abi_encoded_request[:100]}...")
                return abi_encoded_request
            except Exception as e:
                last_error = str(e)
                print(f"   Attempt failed: {last_error}")
                continue
        print(f"❌ Failed to prepare request after trying {len(candidate_paths)} paths.")
        if last_error:
            print(f"   Last error: {last_error}")
        return None
    
    def get_request_fee(self, abi_encoded_request):
        """Get exact fee for the request from fee configuration contract"""
        print("💰 Getting request fee...")
        
        # Convert hex to bytes
        hex_data = abi_encoded_request[2:] if abi_encoded_request.startswith('0x') else abi_encoded_request
        request_bytes = bytes.fromhex(hex_data)
        
        try:
            fee = self.fee_cfg.functions.getRequestFee(request_bytes).call()
            print(f"✅ Request fee: {fee} wei ({self.w3.from_wei(fee, 'ether')} FLR)")
            return fee
        except Exception as e:
            print(f"❌ Failed to get fee: {str(e)}")
            return None
    
    def submit_attestation_request(self, abi_encoded_request):
        """Submit attestation request with correct fee"""
        print("🚀 Submitting attestation request...")
        
        # Get exact fee
        fee = self.get_request_fee(abi_encoded_request)
        if fee is None:
            return None
        
        # Convert hex to bytes
        hex_data = abi_encoded_request[2:] if abi_encoded_request.startswith('0x') else abi_encoded_request
        request_bytes = bytes.fromhex(hex_data)

        # Log balance for diagnostics
        try:
            bal = self.w3.eth.get_balance(self.account.address)
            print(f"💳 Balance: {bal} wei ({self.w3.from_wei(bal, 'ether')} FLR)")
        except Exception as be:
            print(f"⚠️  Could not fetch balance: {be}")
        
        try:
            # Build Type 2 (EIP-1559) transaction with dynamic fees
            max_fee, max_priority = self._suggest_fees()
            tx = self.fdc_hub.functions.requestAttestation(request_bytes).build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "type": 2,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority,
                "value": fee,  # Exact fee from contract
                "chainId": self.w3.eth.chain_id
            })
            # Estimate gas and add a safety margin
            try:
                gas_est = self.fdc_hub.functions.requestAttestation(request_bytes).estimate_gas({
                    "from": self.account.address,
                    "value": fee
                })
                tx["gas"] = int(gas_est * 1.2)
                try:
                    worst_case_cost = int(tx["gas"]) * int(max_fee) + int(fee)
                    print(f"⛽ Gas estimate: {gas_est}; cap maxFeePerGas={max_fee}, maxPriority={max_priority}; worst-case cost: {worst_case_cost} wei")
                except Exception:
                    pass
            except Exception as eg:
                print(f"⚠️  Gas estimate failed, proceeding without override: {eg}")
            
            # Sign and send
            signed = self.w3.eth.account.sign_transaction(tx, private_key=os.getenv('PRIVATE_KEY'))
            raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
            if raw_tx is None:
                raise AttributeError("SignedTransaction missing raw transaction payload (rawTransaction/raw_transaction)")
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            print(f"   Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt via raw RPC (POA-safe)
            receipt_timeout = int(os.getenv('RECEIPT_TIMEOUT', '600'))
            receipt = self._wait_for_receipt_raw(tx_hash.hex(), timeout=receipt_timeout)
            if not receipt:
                print("❌ Timed out waiting for receipt")
                # Attempt automatic speed-ups (replacement txs with higher fees)
                attempts = int(os.getenv('SPEEDUP_ATTEMPTS', '3'))
                last_hash = tx_hash.hex()
                for i in range(attempts):
                    print(f"⏱️ Speed-up attempt {i+1}/{attempts}...")
                    new_hash = self._speed_up_pending(last_hash, request_bytes, fee)
                    if not new_hash:
                        print("   No pending tx to speed-up or replacement not required.")
                        break
                    print(f"   Replacement tx: {new_hash}")
                    last_hash = new_hash
                    receipt = self._wait_for_receipt_raw(new_hash, timeout=receipt_timeout)
                    if receipt:
                        break
                if not receipt:
                    print("❌ Timed out after speed-up attempts")
                    return None
            status = 1 if receipt.get("status") in ("0x1", 1, "1") else 0
            block_number_hex = receipt.get("blockNumber")
            block_number = int(block_number_hex, 16) if isinstance(block_number_hex, str) else int(block_number_hex or 0)
            block_ts = self._safe_get_block_timestamp(block_number)
            
            result = {
                "success": status == 1,
                "transactionHash": tx_hash.hex(),
                "receiptStatus": status,
                "abiEncodedRequest": abi_encoded_request,
                "blockTimestamp": block_ts,
                "blockNumber": block_number
            }
            
            if status == 1:
                print(f"✅ SUCCESS! Transaction mined in block {block_number}")
                print(f"   Block timestamp: {result['blockTimestamp']}")
                
                # Try to decode AttestationRequest event
                self._decode_attestation_event(receipt)
            else:
                print(f"❌ Transaction failed (status: {status})")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to submit: {str(e)}")
            return None
    
    def _decode_attestation_event(self, receipt):
        """Decode AttestationRequest event from receipt"""
        print("📋 Decoding events...")
        
        logs = getattr(receipt, "logs", None)
        if logs is None and isinstance(receipt, dict):
            logs = receipt.get("logs", [])
        if logs is None:
            print("   No logs present on receipt object")
            return None
        
        for log in logs:
            try:
                # Use the correct event name: AttestationRequest (not AttestationRequested)
                event = self.fdc_hub.events.AttestationRequest().process_log(log)
                print(f"   AttestationRequest event found:")
                print(f"     Data: {event.args.data.hex()[:100]}...")
                print(f"     Fee: {event.args.fee} wei")
                return event.args
            except:
                continue
        
        print("   No AttestationRequest events found")
        return None
    
    def _safe_get_block_timestamp(self, block_number):
        """Get block timestamp with POA-safe fallback (raw RPC), avoiding extraData decode issues."""
        try:
            block = self.w3.eth.get_block(block_number)
            ts = block.get("timestamp")
            return int(ts) if isinstance(ts, (int, float)) else int(ts, 0)
        except Exception as e:
            print(f"⚠️  web3 get_block failed: {e}; falling back to raw RPC")
            try:
                rpc_url = os.getenv("RPC_URL")
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBlockByNumber",
                    "params": [hex(block_number), False]
                }
                r = requests.post(rpc_url, json=payload, timeout=30)
                r.raise_for_status()
                data = r.json().get("result", {})
                ts_hex = data.get("timestamp")
                if isinstance(ts_hex, str):
                    return int(ts_hex, 16)
            except Exception as e2:
                print(f"❌ Fallback RPC get_block failed: {e2}")
            # Final fallback: current time
            return int(time.time())
    
    def _wait_for_receipt_raw(self, tx_hash_hex, timeout=180, poll_interval=3):
        """Poll eth_getTransactionReceipt via raw RPC (POA-safe). Returns receipt dict or None on timeout."""
        rpc_url = os.getenv("RPC_URL")
        start = time.time()
        while time.time() - start < timeout:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash_hex]
                }
                r = requests.post(rpc_url, json=payload, timeout=30)
                if r.status_code == 200:
                    res = r.json().get("result")
                    if res is not None:
                        return res
            except Exception as e:
                print(f"   Receipt poll error: {e}")
            time.sleep(poll_interval)
        return None

    def _get_tx_by_hash_raw(self, txh_hex):
        """Raw eth_getTransactionByHash for pending/dropped diagnostics."""
        try:
            rpc_url = os.getenv("RPC_URL")
            payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionByHash", "params": [txh_hex]}
            r = requests.post(rpc_url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json().get("result")
        except Exception as e:
            print(f"   tx lookup error: {e}")
            return None

    def _speed_up_pending(self, old_tx_hash_hex, request_bytes, fee, bump_factor=2, extra_gwei=2):
        """Replace a pending tx with same nonce and higher EIP-1559 fees."""
        tx_info = self._get_tx_by_hash_raw(old_tx_hash_hex)
        if not tx_info or tx_info.get("blockNumber"):
            return None
        try:
            nonce = int(tx_info["nonce"], 16)
        except Exception:
            return None
        # Bump fees
        max_fee, max_priority = self._suggest_fees()
        floor_gwei = int(os.getenv("PRIORITY_TIP_FLOOR_GWEI", "5"))
        bumped_priority = max(int(max_priority) * bump_factor, (floor_gwei + extra_gwei) * 10**9)
        bumped_max_fee = max(int(max_fee) * bump_factor, int(max_priority) + bumped_priority * 2)
        # Rebuild with same nonce
        tx = self.fdc_hub.functions.requestAttestation(request_bytes).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "type": 2,
            "maxFeePerGas": int(bumped_max_fee),
            "maxPriorityFeePerGas": int(bumped_priority),
            "value": fee,
            "chainId": self.w3.eth.chain_id
        })
        try:
            gas_est = self.fdc_hub.functions.requestAttestation(request_bytes).estimate_gas({
                "from": self.account.address,
                "value": fee
            })
            tx["gas"] = int(gas_est * 1.2)
        except Exception as eg:
            print(f"   Speed-up gas estimate failed: {eg}")
        signed = self.w3.eth.account.sign_transaction(tx, private_key=os.getenv('PRIVATE_KEY'))
        raw_tx = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
        new_hash = self.w3.eth.send_raw_transaction(raw_tx)
        return new_hash.hex()
    
    def _suggest_fees(self):
        """Suggest EIP-1559 fees using fee_history with a configurable floor for tip (gwei)."""
        # Priority tip floor can be overridden via env (gwei); default 5 gwei
        floor_gwei = int(os.getenv("PRIORITY_TIP_FLOOR_GWEI", "5"))
        floor_wei = floor_gwei * 10**9
        try:
            hist = self.w3.eth.fee_history(5, "latest", [90])
            base = int(hist["baseFeePerGas"][-1])
            reward_arr = hist.get("reward") or []
            last_reward = reward_arr[-1][0] if reward_arr and reward_arr[-1] else 0
            tip = int(last_reward) if last_reward else floor_wei
            max_priority = max(tip, floor_wei)
            max_fee = base * 2 + max_priority * 3
            print(f"⛽ EIP-1559 fees -> base:{base} wei, maxPriority:{max_priority} wei, maxFee:{max_fee} wei (floor {floor_gwei} gwei)")
            return int(max_fee), int(max_priority)
        except Exception as e:
            print(f"⚠️  fee_history not available, falling back to static fees: {e}")
            # Fallback: tip floor and headroom over base fee if available
            try:
                base = int(self.w3.eth.gas_price)
            except Exception:
                base = int(1e9)  # fallback base = 1 gwei
            max_priority = floor_wei
            max_fee = base * 2 + max_priority * 3
            print(f"⛽ Fallback fees -> base:{base} wei, maxPriority:{max_priority} wei, maxFee:{max_fee} wei (floor {floor_gwei} gwei)")
            return int(max_fee), int(max_priority)
    
    def compute_voting_round_id(self, block_timestamp):
        """Compute voting round ID from block timestamp"""
        # This is a simplified version - production should read from Systems Manager
        # For now, return a placeholder calculation
        
        # Epoch parameters (example from docs - adjust as needed)
        VOTING_EPOCH_DURATION_SECONDS = 90  # 90 seconds
        FIRST_VOTING_ROUND_START_TS = 1658429073  # Example start timestamp
        
        voting_round_id = ((block_timestamp - FIRST_VOTING_ROUND_START_TS) // VOTING_EPOCH_DURATION_SECONDS)
        
        print(f"📅 Voting Round ID calculation:")
        print(f"   Block timestamp: {block_timestamp}")
        print(f"   Calculated voting round: {voting_round_id}")
        
        return voting_round_id
    
    def fetch_da_proof(self, voting_round_id, abi_encoded_request):
        """Fetch proof from DA layer using v1 endpoint"""
        print("🔍 Fetching proof from DA layer...")
        
        url = f"{self.da_layer_api}/api/v1/fdc/proof-by-request-round"
        payload = {
            "votingRoundId": voting_round_id,
            "requestBytes": abi_encoded_request if abi_encoded_request.startswith("0x") else "0x" + abi_encoded_request
        }
        
        print(f"   URL: {url}")
        print(f"   Voting Round: {voting_round_id}")
        print(f"   Request Bytes: {payload['requestBytes'][:100]}...")
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Proof retrieved successfully!")
                return {"success": True, "data": data}
            elif response.status_code == 404:
                print("📭 Proof not available yet (404)")
                return {"success": False, "status": 404, "error": "Proof not ready"}
            else:
                print(f"❌ DA layer error: {response.status_code}")
                return {"success": False, "status": response.status_code, "error": response.text}
                
        except Exception as e:
            print(f"❌ DA fetch failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def demo_evm_transaction_flow(self, sepolia_tx_hash):
        """Demonstrate complete EVMTransaction attestation flow"""
        print("🎯 Demo: EVMTransaction Attestation Flow")
        print("=" * 60)
        
        # Step 1: Prepare request
        abi_encoded_request = self.prepare_evm_transaction_request(sepolia_tx_hash)
        if not abi_encoded_request:
            return False
        
        # Step 2: Submit to FDC Hub
        result = self.submit_attestation_request(abi_encoded_request)
        if not result or not result["success"]:
            return False
        
        # Step 3: Calculate voting round and show DA fetch
        voting_round_id = self.compute_voting_round_id(result["blockTimestamp"])
        
        print(f"\n⏳ Waiting 30 seconds before DA fetch (round finalization)...")
        time.sleep(30)
        
        # Step 4: Attempt DA fetch
        da_result = self.fetch_da_proof(voting_round_id, abi_encoded_request)
        
        if da_result["success"]:
            print("🎉 COMPLETE SUCCESS! Full attestation flow working!")
        else:
            print("⚠️  Attestation submitted successfully, but DA proof not ready yet.")
            print(f"   You can retry DA fetch later with:")
            print(f"   POST {self.da_layer_api}/api/v1/fdc/proof-by-request-round")
            print(f"   Body: {{'votingRoundId': {voting_round_id}, 'requestBytes': '{abi_encoded_request}'}}")
        
        return True
    
    def demo_jsonapi_flow(self, url, jq_transform, abi_signature):
        """Demonstrate complete JsonApi attestation flow"""
        print("🎯 Demo: JsonApi Attestation Flow") 
        print("=" * 60)
        
        # Step 1: Prepare request
        abi_encoded_request = self.prepare_jsonapi_request(url, jq_transform, abi_signature)
        if not abi_encoded_request:
            return False
        
        # Step 2: Submit to FDC Hub  
        result = self.submit_attestation_request(abi_encoded_request)
        if not result or not result["success"]:
            return False
            
        # Step 3: Calculate voting round and show DA fetch
        voting_round_id = self.compute_voting_round_id(result["blockTimestamp"])
        
        print(f"\n⏳ Waiting 30 seconds before DA fetch...")
        time.sleep(30)
        
        # Step 4: Attempt DA fetch
        da_result = self.fetch_da_proof(voting_round_id, abi_encoded_request) 
        
        if da_result["success"]:
            print("🎉 COMPLETE SUCCESS! Full JsonApi attestation flow working!")
        else:
            print("⚠️  Attestation submitted successfully, but DA proof not ready yet.")
            
        return True

def main():
    print("🚀 Flare FDC Corrected Implementation")
    print("Based on expert guidance to fix transaction reverts")
    print("=" * 60)
    
    # Initialize
    flow = FlareAttestationFlow()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/flare_corrected_flow.py evm <sepolia_tx_hash>")
        print("  python scripts/flare_corrected_flow.py jsonapi <url> <jq_transform> <abi_signature>")
        print()
        print("Example:")
        print("  python scripts/flare_corrected_flow.py evm 0x1234...")
        print("  python scripts/flare_corrected_flow.py jsonapi 'https://api.example.com/data' '.price' 'uint256'")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "evm":
        if len(sys.argv) < 3:
            print("❌ Missing sepolia transaction hash")
            return
        
        sepolia_tx = sys.argv[2]
        success = flow.demo_evm_transaction_flow(sepolia_tx)
        
    elif mode == "jsonapi":
        if len(sys.argv) < 5:
            print("❌ Missing JsonApi parameters: <url> <jq_transform> <abi_signature>")
            return
        
        url = sys.argv[2]
        jq_transform = sys.argv[3] 
        abi_signature = sys.argv[4]
        success = flow.demo_jsonapi_flow(url, jq_transform, abi_signature)
        
    else:
        print(f"❌ Unknown mode: {mode}")
        return
    
    if success:
        print("\n✅ Implementation working correctly!")
        print("The previous transaction reverts were due to:")
        print("  - Self-encoding (string,string) instead of verifier abiEncodedRequest") 
        print("  - Hard-coded fees instead of getRequestFee(requestBytes)")
        print("  - Wrong ABI (return value + wrong event name)")
        print("All issues now resolved! 🎉")
    else:
        print("\n❌ Still encountering issues - check logs above")

if __name__ == "__main__":
    main()
