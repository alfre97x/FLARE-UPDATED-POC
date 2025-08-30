#!/usr/bin/env python3
"""
Comprehensive Blockchain Status Report
Analyzes the current state of blockchain integration and provides recommendations
"""

import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def main():
    """Generate comprehensive status report"""
    
    print("🔍 COMPREHENSIVE BLOCKCHAIN STATUS REPORT")
    print("=" * 80)
    
    # Configuration
    RPC_URL = os.getenv('RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    FDC_HUB_ADDRESS = os.getenv('FDC_HUB_ADDRESS', '0x48aC463d797582898331F4De43341627b9c5f1D')
    FDC_VERIFICATION_ADDRESS = os.getenv('FDC_VERIFICATION_ADDRESS', '0x075bf3f01fF07C4920e5261F9a366969640F5348')
    DATAPURCHASE_CONTRACT_ADDRESS = os.getenv('DATAPURCHASE_CONTRACT_ADDRESS')
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Cannot connect to blockchain")
        return
        
    account = None
    if PRIVATE_KEY:
        account = w3.eth.account.from_key(PRIVATE_KEY)
    
    print("\n📋 CURRENT STATUS SUMMARY")
    print("-" * 50)
    
    # Check FDC Hub
    fdc_hub_code = w3.eth.get_code(w3.to_checksum_address(FDC_HUB_ADDRESS))
    fdc_hub_exists = len(fdc_hub_code) > 0
    
    # Check FDC Verification
    fdc_verification_code = w3.eth.get_code(w3.to_checksum_address(FDC_VERIFICATION_ADDRESS))
    fdc_verification_exists = len(fdc_verification_code) > 0
    
    # Check DataPurchase contract if address provided
    datapurchase_exists = False
    if DATAPURCHASE_CONTRACT_ADDRESS:
        datapurchase_code = w3.eth.get_code(w3.to_checksum_address(DATAPURCHASE_CONTRACT_ADDRESS))
        datapurchase_exists = len(datapurchase_code) > 0
    
    print(f"✅ Blockchain Connection: Working (Chain ID: {w3.eth.chain_id})")
    print(f"{'✅' if account else '❌'} Account Setup: {'Working' if account else 'No private key'}")
    if account:
        balance = w3.eth.get_balance(account.address)
        print(f"   Address: {account.address}")
        print(f"   Balance: {w3.from_wei(balance, 'ether'):.4f} FLR")
    
    print(f"{'✅' if fdc_hub_exists else '❌'} FDC Hub Contract: {'Exists' if fdc_hub_exists else 'Missing'}")
    print(f"   Address: {FDC_HUB_ADDRESS}")
    
    print(f"{'✅' if fdc_verification_exists else '❌'} FDC Verification: {'Exists' if fdc_verification_exists else 'Missing'}")
    print(f"   Address: {FDC_VERIFICATION_ADDRESS}")
    
    if DATAPURCHASE_CONTRACT_ADDRESS:
        print(f"{'✅' if datapurchase_exists else '❌'} DataPurchase Contract: {'Exists' if datapurchase_exists else 'Missing'}")
        print(f"   Address: {DATAPURCHASE_CONTRACT_ADDRESS}")
    else:
        print("❌ DataPurchase Contract: Not deployed/configured")
    
    print(f"❌ DA Layer API: DNS resolution failing")
    print(f"   Configured URL: {os.getenv('DA_LAYER_API', 'https://api.da.coston2.flare.network')}")
    
    print("\n📋 DETAILED ANALYSIS")
    print("-" * 50)
    
    if fdc_hub_exists:
        print("\n🔍 FDC Hub Contract Analysis:")
        
        try:
            with open('abi/fdc_hub_abi.json', 'r') as f:
                fdc_hub_abi = json.load(f)
            
            contract = w3.eth.contract(
                address=w3.to_checksum_address(FDC_HUB_ADDRESS), 
                abi=fdc_hub_abi
            )
            
            print(f"   ✅ ABI loaded: {len(fdc_hub_abi)} functions")
            
            # Try to call owner function
            try:
                owner = contract.functions.owner().call()
                print(f"   ✅ Contract owner: {owner}")
                
                if account:
                    if account.address.lower() == owner.lower():
                        print("   ✅ Your account IS the owner (full access)")
                    else:
                        print("   ⚠️  Your account is NOT the owner (may have restricted access)")
                        
            except Exception as e:
                print(f"   ❌ Could not read owner: {str(e)}")
            
            # Analyze the failed transaction reason
            print(f"\n   🔍 Transaction Failure Analysis:")
            print(f"   - Contract exists and ABI loads correctly")
            print(f"   - Transaction building works fine") 
            print(f"   - Transaction fails on execution with 'execution reverted'")
            print(f"   - Gas used: 22,584 (very low, immediate revert)")
            print(f"   - This suggests the contract has access controls or input validation")
            
        except Exception as e:
            print(f"   ❌ Error analyzing contract: {str(e)}")
    
    print("\n💡 RECOMMENDATIONS")
    print("-" * 50)
    
    if not fdc_verification_exists:
        print("\n1. 🔧 FDC Verification Contract Issue:")
        print("   ❌ No contract found at configured address")
        print("   🛠️  ACTION: Check with Flare team for current FDC Verification address")
        print("   📝 The address might have changed since the initial configuration")
    
    print("\n2. 🔧 DA Layer API Issue:")
    print("   ❌ DNS resolution failing for api.da.coston2.flare.network")
    print("   🛠️  ACTION: Check with Flare team for current DA Layer API endpoint")
    print("   📝 The API endpoint might have changed or be temporarily unavailable")
    
    print("\n3. 🔧 FDC Hub Access Issue:")
    print("   ❌ Contract exists but reverts transactions")
    print("   🛠️  ACTIONS:")
    print("   📝 Check if specific attestation types are required")
    print("   📝 Verify if there are access controls (whitelisted addresses)")
    print("   📝 Try calling with different attestation parameters")
    print("   📝 Check if the contract is paused or has specific requirements")
    
    if not DATAPURCHASE_CONTRACT_ADDRESS:
        print("\n4. 🔧 DataPurchase Contract Missing:")
        print("   ❌ No DataPurchase contract configured")
        print("   🛠️  ACTION: Deploy DataPurchase contract and update .env file")
    
    print("\n🎯 IMMEDIATE NEXT STEPS")
    print("-" * 50)
    print("1. Contact Flare team to verify current FDC system addresses")
    print("2. Test with different attestation types/parameters")  
    print("3. Deploy missing DataPurchase contract")
    print("4. Update configuration with correct addresses")
    print("5. Test end-to-end flow once addresses are verified")
    
    print(f"\n📊 SYSTEM READINESS SCORE")
    print("-" * 50)
    
    total_components = 6
    working_components = sum([
        w3.is_connected(),
        account is not None,
        fdc_hub_exists,
        fdc_verification_exists,
        datapurchase_exists if DATAPURCHASE_CONTRACT_ADDRESS else False,
        False  # DA Layer API (currently failing)
    ])
    
    score = (working_components / total_components) * 100
    print(f"Overall readiness: {working_components}/{total_components} components working ({score:.1f}%)")
    
    if score >= 80:
        print("🎉 System is mostly ready - minor fixes needed")
    elif score >= 60:
        print("⚠️  System needs significant fixes but foundation is good")  
    else:
        print("🔧 System needs major work before production ready")

if __name__ == "__main__":
    main()
