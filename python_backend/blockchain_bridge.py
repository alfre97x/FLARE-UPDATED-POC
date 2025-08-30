"""
Blockchain Bridge for SpaceData application
Provides Flask routes to interact with the blockchain API
"""

import json
import logging
from flask import Blueprint, jsonify, request
from blockchain_api import BlockchainAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api/blockchain')

@blockchain_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get blockchain configuration
    
    Returns:
        JSON response with blockchain configuration
    """
    try:
        config = BlockchainAPI.get_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting blockchain config: {str(e)}")
        return jsonify({
            "error": "Failed to get blockchain configuration",
            "details": str(e)
        }), 500

@blockchain_bp.route('/request-attestation', methods=['POST'])
def request_attestation():
    """
    Request attestation from FDC Hub
    
    Request body:
        attestation_type: Type of attestation
        parameters: Parameters for attestation
        
    Returns:
        JSON response with transaction result
    """
    try:
        data = request.json
        
        if not data or 'attestation_type' not in data or 'parameters' not in data:
            return jsonify({
                "error": "Missing required parameters",
                "details": "attestation_type and parameters are required"
            }), 400
        
        attestation_type = data['attestation_type']
        parameters = data['parameters']
        
        result = BlockchainAPI.request_attestation(attestation_type, parameters)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                "error": "Failed to request attestation",
                "details": result.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        logger.error(f"Error requesting attestation: {str(e)}")
        return jsonify({
            "error": "Failed to request attestation",
            "details": str(e)
        }), 500

@blockchain_bp.route('/fetch-attestation/<request_id>', methods=['GET'])
def fetch_attestation(request_id):
    """
    Fetch attestation result from DA Layer API
    
    Path parameters:
        request_id: Request ID
        
    Returns:
        JSON response with attestation result
    """
    try:
        result = BlockchainAPI.fetch_attestation_result(request_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                "error": "Failed to fetch attestation result",
                "details": result.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        logger.error(f"Error fetching attestation result: {str(e)}")
        return jsonify({
            "error": "Failed to fetch attestation result",
            "details": str(e)
        }), 500

@blockchain_bp.route('/verify-attestation', methods=['POST'])
def verify_attestation():
    """
    Verify attestation using FDC Verification contract
    
    Request body:
        request_id: Request ID
        attestation_response: Attestation response
        proof: Proof
        
    Returns:
        JSON response with verification result
    """
    try:
        data = request.json
        
        if not data or 'request_id' not in data or 'attestation_response' not in data or 'proof' not in data:
            return jsonify({
                "error": "Missing required parameters",
                "details": "request_id, attestation_response, and proof are required"
            }), 400
        
        request_id = data['request_id']
        attestation_response = data['attestation_response']
        proof = data['proof']
        
        result = BlockchainAPI.verify_attestation(request_id, attestation_response, proof)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                "error": "Failed to verify attestation",
                "details": result.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        logger.error(f"Error verifying attestation: {str(e)}")
        return jsonify({
            "error": "Failed to verify attestation",
            "details": str(e)
        }), 500

@blockchain_bp.route('/deliver-data', methods=['POST'])
def deliver_data():
    """
    Deliver data to DataPurchase contract
    
    Request body:
        request_id: Request ID
        attestation_response: Attestation response
        proof: Proof
        
    Returns:
        JSON response with transaction result
    """
    try:
        data = request.json
        
        if not data or 'request_id' not in data or 'attestation_response' not in data or 'proof' not in data:
            return jsonify({
                "error": "Missing required parameters",
                "details": "request_id, attestation_response, and proof are required"
            }), 400
        
        request_id = data['request_id']
        attestation_response = data['attestation_response']
        proof = data['proof']
        
        result = BlockchainAPI.deliver_data(request_id, attestation_response, proof)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                "error": "Failed to deliver data",
                "details": result.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        logger.error(f"Error delivering data: {str(e)}")
        return jsonify({
            "error": "Failed to deliver data",
            "details": str(e)
        }), 500

@blockchain_bp.route('/generate-request-id', methods=['POST'])
def generate_request_id():
    """
    Generate a request ID for a data request
    
    Request body:
        data_info: Dictionary with data information
        
    Returns:
        JSON response with request ID
    """
    try:
        data = request.json
        
        if not data or 'data_info' not in data:
            return jsonify({
                "error": "Missing required parameters",
                "details": "data_info is required"
            }), 400
        
        data_info = data['data_info']
        
        request_id = BlockchainAPI.generate_request_id(data_info)
        
        return jsonify({
            "success": True,
            "requestId": request_id
        })
    except Exception as e:
        logger.error(f"Error generating request ID: {str(e)}")
        return jsonify({
            "error": "Failed to generate request ID",
            "details": str(e)
        }), 500
