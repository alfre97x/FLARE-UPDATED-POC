#!/usr/bin/env python3
"""
Investigate the failed FDC Hub transaction
"""

import os
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Configuration
RPC_URL = os.getenv('RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
TX_HASH = "0x3ea80d6883058ccdf66cff34227122dc0a8e4b1cec860b04fd402e6b2e1e5194"

def main():
    """Investigate the failed transaction"""
    print(f"🔍 Investigating failed transaction: {TX_HASH}")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Cannot connect to blockchain")
        return
    
    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(TX_HASH)
        
        print(f"\n📋 Transaction Receipt:")
        print(f"   Status: {receipt.status} ({'✅ Success' if receipt.status == 1 else '❌ Failed'})")
        print(f"   Block: {receipt.blockNumber}")
        print(f"   Gas Used: {receipt.gasUsed:,}")
        print(f"   Gas Limit: {receipt.cumulativeGasUsed:,}")
        
        # Get the original transaction
        tx = w3.eth.get_transaction(TX_HASH)
        print(f"\n📋 Transaction Details:")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {tx['value']}")
        print(f"   Gas Price: {tx['gasPrice']:,}")
        print(f"   Gas Limit: {tx['gas']:,}")
        print(f"   Input Data: {tx['input'][:100]}...")
        
        # Analyze the logs
        print(f"\n📋 Transaction Logs:")
        if receipt.logs:
            for i, log in enumerate(receipt.logs):
                print(f"   Log {i}: {log}")
        else:
            print("   No logs (transaction reverted)")
        
        # Try to get revert reason if possible
        print(f"\n🔍 Attempting to get revert reason...")
        try:
            # Replay the transaction to get the revert reason
            result = w3.eth.call({
                'to': tx['to'],
                'from': tx['from'],
                'data': tx['input'],
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'value': tx['value']
            }, tx['blockNumber'] - 1)
            print(f"   Call result: {result}")
        except Exception as e:
            print(f"   Revert reason: {str(e)}")
            
        # Check if we can decode the input data
        print(f"\n🔍 Decoding transaction input...")
        try:
            # Load FDC Hub ABI
            with open('abi/fdc_hub_abi.json', 'r') as f:
                fdc_hub_abi = json.load(f)
            
            contract = w3.eth.contract(address=tx['to'], abi=fdc_hub_abi)
            
            # Decode the input data
            decoded = contract.decode_function_input(tx['input'])
            print(f"   Function: {decoded[0].function_identifier}")
            print(f"   Inputs: {decoded[1]}")
            
        except Exception as e:
            print(f"   Could not decode input: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error investigating transaction: {str(e)}")

if __name__ == "__main__":
    main()
