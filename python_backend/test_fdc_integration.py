"""
Test script for the new FDC Integration
Tests the proper Flare FDC workflow with real satellite data
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fdc_integration import FDCIntegration
    from copernicus_api import search_satellite_data
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_contract_resolution():
    """Test that we can resolve contracts via Contract Registry"""
    print("\n=== Step 1: Testing Contract Resolution ===")
    
    fdc = FDCIntegration()
    
    # Get contract addresses
    addresses = fdc.get_contract_addresses()
    
    print("📋 Resolved Contract Addresses:")
    for name, address in addresses.items():
        status = "✅" if address.startswith("0x") and len(address) == 42 else "❌"
        print(f"   {status} {name}: {address}")
    
    return len([addr for addr in addresses.values() if addr.startswith("0x") and len(addr) == 42]) >= 2

def test_evm_transaction_preparation():
    """Test EVMTransaction request preparation (for validation first)"""
    print("\n=== Step 2A: Testing EVMTransaction Request Preparation ===")
    
    fdc = FDCIntegration()
    
    # Use a known testETH transaction hash
    test_tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    print(f"🔍 Preparing EVMTransaction request:")
    print(f"   Transaction Hash: {test_tx_hash}")
    
    try:
        abi_encoded_request = fdc.prepare_evm_transaction_request(test_tx_hash)
        
        if abi_encoded_request:
            print(f"✅ Successfully prepared EVMTransaction request")
            print(f"   Request length: {len(abi_encoded_request)} bytes")
            print(f"   Request preview: {abi_encoded_request[:32].hex()}...")
            return abi_encoded_request
        else:
            print("❌ Failed to prepare EVMTransaction request")
            return None
            
    except Exception as e:
        print(f"❌ Error preparing EVMTransaction request: {e}")
        return None

def test_jsonapi_preparation():
    """Test JsonApi request preparation"""
    print("\n=== Step 2B: Testing JsonApi Request Preparation ===")
    
    fdc = FDCIntegration()
    
    # Test with httpbin.org which returns predictable JSON
    test_url = "https://httpbin.org/json"
    test_jq = "{slideshow_title: .slideshow.title, author: .slideshow.author}"
    test_abi = "tuple(string slideshow_title,string author)"
    
    print(f"🔍 Preparing JsonApi request:")
    print(f"   URL: {test_url}")
    print(f"   JQ Expression: {test_jq}")
    print(f"   ABI Signature: {test_abi}")
    
    try:
        abi_encoded_request = fdc.prepare_jsonapi_request(test_url, test_jq, test_abi)
        
        if abi_encoded_request:
            print(f"✅ Successfully prepared JsonApi request")
            print(f"   Request length: {len(abi_encoded_request)} bytes")
            print(f"   Request preview: {abi_encoded_request[:32].hex()}...")
            return abi_encoded_request
        else:
            print("❌ Failed to prepare JsonApi request")
            return None
            
    except Exception as e:
        print(f"❌ Error preparing JsonApi request: {e}")
        return None

def test_fee_calculation(abi_encoded_request):
    """Test fee calculation"""
    print("\n=== Step 3: Testing Fee Calculation ===")
    
    if not abi_encoded_request:
        print("❌ No request data available for fee calculation")
        return 0
    
    fdc = FDCIntegration()
    
    try:
        fee = fdc.get_request_fee(abi_encoded_request)
        
        if fee > 0:
            print(f"✅ Fee calculated successfully")
            print(f"   Fee: {fee} wei ({fee / 10**18:.6f} FLR)")
            return fee
        else:
            print("❌ Fee calculation returned 0")
            return 0
            
    except Exception as e:
        print(f"❌ Error calculating fee: {e}")
        return 0

def test_full_attestation_flow():
    """Test the complete attestation flow"""
    print("\n=== Step 4: Testing Full Attestation Flow ===")
    
    fdc = FDCIntegration()
    
    # Use a simple test URL for Web2Json attestation
    test_url = "https://httpbin.org/json"
    json_path = "$.slideshow.title"
    
    print(f"🚀 Starting full attestation flow")
    print(f"   URL: {test_url}")
    print(f"   JSON Path: {json_path}")
    
    try:
        # Prepare request
        abi_encoded_request = fdc.prepare_web2json_request(test_url, json_path)
        
        if not abi_encoded_request:
            print("❌ Failed to prepare request")
            return False
        
        print("✅ Request prepared successfully")
        
        # Submit attestation
        result = fdc.request_attestation(abi_encoded_request)
        
        print("📋 Attestation Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Attestation submitted successfully!")
            print(f"🔗 Transaction Hash: {result.get('transactionHash')}")
            print(f"🆔 Request ID: {result.get('requestId')}")
            print(f"💰 Fee Paid: {result.get('fee', 0) / 10**18:.6f} FLR")
            return result.get('requestId')
        else:
            print("❌ Attestation failed")
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error in attestation flow: {e}")
        return False

def test_satellite_data_attestation():
    """Test attesting real satellite data"""
    print("\n=== Step 5: Testing Satellite Data Attestation ===")
    
    # Get some real satellite data
    print("🛰️  Fetching real satellite data...")
    
    try:
        # Use Copenhagen as test location
        coords = [[55.6761, 12.5683], [55.6661, 12.5783], [55.6861, 12.5883]]
        results = search_satellite_data(
            data_type='S2MSI2A',
            coordinates=coords,
            start_date='2025-07-20',
            end_date='2025-07-30',
            cloud_cover_max=15,
            limit=1
        )
        
        if not results:
            print("❌ No satellite data found")
            return False
        
        satellite_data = results[0]
        print(f"✅ Found satellite data: {satellite_data['id']}")
        print(f"   📅 Date: {satellite_data['datetime']}")
        print(f"   ☁️  Cloud Cover: {satellite_data.get('cloud_cover', 'N/A')}%")
        
        # Test attestation with satellite data
        fdc = FDCIntegration()
        result = fdc.attest_satellite_data(satellite_data)
        
        print("📋 Satellite Data Attestation Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Satellite data attestation successful!")
            return True
        else:
            print("❌ Satellite data attestation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in satellite data attestation: {e}")
        return False

def test_da_layer_fetch(request_id):
    """Test fetching results from DA Layer"""
    print("\n=== Step 6: Testing DA Layer Result Fetch ===")
    
    if not request_id:
        print("❌ No request ID available for DA Layer test")
        return False
    
    fdc = FDCIntegration()
    
    print(f"⏳ Waiting 30 seconds for FDC processing...")
    time.sleep(30)
    
    try:
        result = fdc.fetch_attestation_result(request_id)
        
        print("📋 DA Layer Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Successfully fetched attestation result!")
            return True
        else:
            print("❌ Failed to fetch attestation result")
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching DA Layer result: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive FDC integration test"""
    
    print("🚀 Starting Comprehensive FDC Integration Test")
    print("=" * 80)
    
    # Track test results
    test_results = []
    
    # Step 1: Contract Resolution
    result1 = test_contract_resolution()
    test_results.append(("Contract Resolution", result1))
    
    # Step 2A: EVMTransaction Request Preparation (test first)
    evm_request = test_evm_transaction_preparation()
    result2a = evm_request is not None
    test_results.append(("EVMTransaction Preparation", result2a))
    
    # Step 2B: JsonApi Request Preparation
    jsonapi_request = test_jsonapi_preparation()
    result2b = jsonapi_request is not None
    test_results.append(("JsonApi Preparation", result2b))
    
    # Use whichever request worked for fee testing
    abi_request = evm_request if evm_request else jsonapi_request
    result2 = abi_request is not None
    
    # Step 3: Fee Calculation
    fee = test_fee_calculation(abi_request) if abi_request else 0
    result3 = fee > 0
    test_results.append(("Fee Calculation", result3))
    
    # Step 4: Full Attestation Flow (only if previous tests passed)
    request_id = None
    if result1 and result2 and result3:
        request_id = test_full_attestation_flow()
        result4 = request_id is not False
    else:
        result4 = False
        print("\n=== Step 4: SKIPPED (prerequisites failed) ===")
    
    test_results.append(("Full Attestation Flow", result4))
    
    # Step 5: Satellite Data Attestation
    result5 = test_satellite_data_attestation()
    test_results.append(("Satellite Data Attestation", result5))
    
    # Step 6: DA Layer Fetch (only if we have a request ID)
    if request_id:
        result6 = test_da_layer_fetch(request_id)
    else:
        result6 = False
        print("\n=== Step 6: SKIPPED (no request ID) ===")
    
    test_results.append(("DA Layer Result Fetch", result6))
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE FDC INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed_count = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed:
            passed_count += 1
    
    print(f"\n📊 Overall Result: {passed_count}/{len(test_results)} tests passed ({passed_count/len(test_results)*100:.1f}%)")
    
    if passed_count == len(test_results):
        print("🎉 ALL TESTS PASSED - FDC Integration working perfectly!")
    elif passed_count >= len(test_results) // 2:
        print("⚠️  PARTIAL SUCCESS - Core functionality working, some advanced features need attention")
    else:
        print("❌ MAJOR ISSUES - Core FDC integration needs investigation")
    
    return passed_count, len(test_results)

if __name__ == "__main__":
    run_comprehensive_test()
