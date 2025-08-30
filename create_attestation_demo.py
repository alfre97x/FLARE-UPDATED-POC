#!/usr/bin/env python3
"""
Demo script to create a proper FDC attestation and show the complete flow
"""

import requests
import json
import time

# API endpoints
PROXY_BASE_URL = 'http://localhost:3001/api/blockchain'
DA_LAYER_API = 'https://ctn2-data-availability.flare.network'

def create_attestation():
    """Create an attestation using AddressValidity type"""
    print("🚀 Creating FDC Attestation...")
    print("=" * 60)
    
    try:
        # Use AddressValidity - a standard attestation type
        data = {
            "attestation_type": "AddressValidity", 
            "parameters": "0xA68943EdC09bf47e6F6b440239c4a07Cdcef0874"
        }
        
        print(f"📝 Request Details:")
        print(f"   Type: {data['attestation_type']}")
        print(f"   Parameters: {data['parameters']}")
        print(f"   Endpoint: {PROXY_BASE_URL}/request-attestation")
        print()
        
        response = requests.post(
            f"{PROXY_BASE_URL}/request-attestation",
            headers={'Content-Type': 'application/json'},
            json=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Attestation Created!")
            print(f"   Transaction Hash: {result.get('transactionHash')}")
            
            request_id = result.get('requestId')
            if request_id:
                print(f"   Request ID: {request_id}")
                return request_id
            else:
                print("   ⚠️  No requestId in response - checking transaction...")
                return result.get('transactionHash')
        
        elif response.status_code == 500:
            error_data = response.json()
            print("❌ FAILED - Server Error:")
            print(f"   Error: {error_data.get('error')}")
            print(f"   Details: {error_data.get('details')}")
            
            if "Transaction failed (reverted)" in error_data.get('details', ''):
                print("\n💡 Likely causes:")
                print("   - Insufficient fee (increase FDC_REQUEST_FEE_WEI)")
                print("   - Invalid attestation type")
                print("   - FDC Hub not accepting requests")
            
            return None
        
        else:
            print(f"❌ FAILED - Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {str(e)}")
        print("\n💡 Make sure both servers are running:")
        print("   - python python_backend/app.py")
        print("   - node server.js")
        return None

def poll_da_layer(request_id):
    """Poll DA Layer for attestation result"""
    if not request_id or len(request_id) < 32:
        print("⚠️  Invalid request_id for DA polling")
        return None, None
    
    print(f"\n🔍 Polling DA Layer...")
    print("=" * 60)
    
    # Clean request_id (remove 0x if present)
    clean_id = request_id[2:] if request_id.startswith('0x') else request_id
    
    url = f"{DA_LAYER_API}/attestations/{clean_id}"
    print(f"📍 URL: {url}")
    
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"   Attempt {attempt}/{max_attempts}...", end=" ")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS!")
                print(f"   Attestation Response: {result.get('attestationResponse')}")
                print(f"   Proof: {result.get('proof')[:100]}..." if result.get('proof') else "   Proof: None")
                
                return result.get('attestationResponse'), result.get('proof')
            
            elif response.status_code == 404:
                print("📭 Not ready yet")
                if attempt < max_attempts:
                    wait_time = min(5 + attempt, 15)  # Progressive backoff
                    print(f"   Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
            else:
                print(f"❌ Error {response.status_code}")
                return None, None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {str(e)}")
            return None, None
    
    print("\n⏰ Timeout reached - attestation may still be processing")
    return None, None

def verify_attestation(request_id, attestation_response, proof):
    """Verify the attestation on-chain"""
    if not all([request_id, attestation_response, proof]):
        print("⚠️  Missing data for verification")
        return False
    
    print(f"\n✅ Verifying Attestation...")
    print("=" * 60)
    
    try:
        # Clean hex values (remove 0x)
        clean_request_id = request_id[2:] if request_id.startswith('0x') else request_id
        clean_attestation = attestation_response[2:] if attestation_response.startswith('0x') else attestation_response
        clean_proof = proof[2:] if proof.startswith('0x') else proof
        
        data = {
            "request_id": clean_request_id,
            "attestation_response": clean_attestation, 
            "proof": clean_proof
        }
        
        response = requests.post(
            f"{PROXY_BASE_URL}/verify-attestation",
            headers={'Content-Type': 'application/json'},
            json=data,
            timeout=15
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            verified = result.get('verified', False)
            print(f"✅ Verification Result: {'VALID' if verified else 'INVALID'}")
            return verified
        else:
            error_data = response.json()
            print(f"❌ Verification Failed:")
            print(f"   Error: {error_data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Verification Error: {str(e)}")
        return False

def deliver_data(request_id, attestation_response, proof):
    """Deliver data to DataPurchase contract"""
    if not all([request_id, attestation_response, proof]):
        print("⚠️  Missing data for delivery")
        return False
    
    print(f"\n📦 Delivering Data...")
    print("=" * 60)
    
    try:
        # Clean hex values (remove 0x)
        clean_request_id = request_id[2:] if request_id.startswith('0x') else request_id
        clean_attestation = attestation_response[2:] if attestation_response.startswith('0x') else attestation_response
        clean_proof = proof[2:] if proof.startswith('0x') else proof
        
        data = {
            "request_id": clean_request_id,
            "attestation_response": clean_attestation,
            "proof": clean_proof
        }
        
        response = requests.post(
            f"{PROXY_BASE_URL}/deliver-data",
            headers={'Content-Type': 'application/json'},
            json=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            tx_hash = result.get('transactionHash')
            print(f"✅ Data Delivered Successfully!")
            print(f"   Transaction Hash: {tx_hash}")
            return True
        else:
            error_data = response.json()
            print(f"❌ Delivery Failed:")
            print(f"   Error: {error_data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Delivery Error: {str(e)}")
        return False

def main():
    """Run the complete attestation flow"""
    print("🎯 Complete FDC Attestation Flow Demo")
    print("=" * 60)
    print()
    
    # Step 1: Create attestation
    request_id = create_attestation()
    if not request_id:
        print("\n❌ Could not create attestation. Exiting.")
        return
    
    # Step 2: Poll DA Layer
    attestation_response, proof = poll_da_layer(request_id)
    if not attestation_response or not proof:
        print("\n⏰ Attestation not ready yet. You can retry polling later with:")
        print(f"   GET {DA_LAYER_API}/attestations/{request_id}")
        return
    
    # Step 3: Verify attestation
    verified = verify_attestation(request_id, attestation_response, proof)
    if not verified:
        print("\n❌ Attestation verification failed")
        return
    
    # Step 4: Deliver data
    delivered = deliver_data(request_id, attestation_response, proof)
    if delivered:
        print("\n🎉 COMPLETE SUCCESS!")
        print("✅ Attestation created")
        print("✅ DA layer data retrieved") 
        print("✅ On-chain verification passed")
        print("✅ Data delivered to contract")
    else:
        print("\n⚠️  Partial success - attestation works but delivery failed")

if __name__ == "__main__":
    main()
