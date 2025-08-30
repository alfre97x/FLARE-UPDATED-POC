"""
Flask backend for SpaceData application
Handles API requests for Copernicus satellite data and AI features
"""

import os
import json
import logging
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import math

# Import blockchain bridge
from blockchain_bridge import blockchain_bp

# Import AI service
from ai_service import AIService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
# CORS: allow local dev by default; restrict via CORS_ORIGINS in production (comma-separated)
cors_origins = os.environ.get('CORS_ORIGINS')
if cors_origins:
    origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]
    CORS(app, origins=origins_list, supports_credentials=True)
else:
    CORS(app)

# Register blockchain blueprint
app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/blockchain-test')
def blockchain_test():
    """Render the blockchain test page"""
    return render_template('blockchain-test.html')

@app.route('/data-selection')
def data_selection():
    """Render the data selection page"""
    # Get query parameter for AI Assistant suggestion
    query = request.args.get('query', '')
    return render_template('data_selection.html', query=query)

@app.route('/process-selection', methods=['POST'])
def process_selection():
    """Process the data selection form and redirect to results page"""
    # Get form data
    data_type = request.form.get('dataType', 'S2MSI2A')
    start_date = request.form.get('startDate', '2023-04-15')
    end_date = request.form.get('endDate', '2023-04-22')
    coordinates = request.form.get('coordinates', '')
    ai_analysis = 'aiAnalysis' in request.form
    
    # Get transaction hash if provided
    tx_hash = request.form.get('txHash', '')
    request_id = request.form.get('requestId', '')
    
    # If no transaction hash is provided, generate one
    if not tx_hash:
        tx_hash = f"0x{uuid.uuid4().hex[:16]}"
    
    # Redirect to results page with parameters
    return redirect(url_for('data_results', 
                           data_type=data_type,
                           start_date=start_date,
                           end_date=end_date,
                           coordinates=coordinates,
                           ai_analysis=ai_analysis,
                           tx_hash=tx_hash,
                           request_id=request_id))

@app.route('/data-results')
def data_results():
    """Render the data results page"""
    # Get query parameters
    data_type = request.args.get('data_type', 'S2MSI2A')
    start_date = request.args.get('start_date', '2023-04-15')
    end_date = request.args.get('end_date', '2023-04-22')
    coordinates_str = request.args.get('coordinates', '')
    ai_analysis = request.args.get('ai_analysis', 'true').lower() == 'true'
    tx_hash = request.args.get('tx_hash', '0x' + '0' * 16)
    request_id = request.args.get('request_id', '')
    view = request.args.get('view', 'analysis')
    
    # Import the Copernicus API module
    import copernicus_api
    
    # Get real satellite data from Copernicus API
    try:
        # Parse coordinates if provided as string
        coords = coordinates_str
        if coords and isinstance(coords, str):
            try:
                import json
                coords = json.loads(coords)
            except json.JSONDecodeError:
                logger.warning(f"Invalid coordinates format: {coords}")
                coords = None
        
        # Search for satellite data
        satellite_data = copernicus_api.search_satellite_data(
            data_type=data_type,
            coordinates=coords,
            start_date=start_date,
            end_date=end_date,
            cloud_cover_max=100,
            limit=5
        )
        
        # Extract image URLs and metadata
        satellite_image_urls = []
        cloud_cover = 0
        area_size = 100  # Default value
        location_name = "Selected Area"
        
        if satellite_data:
            # Get thumbnail URLs
            for item in satellite_data:
                if item.get('thumbnail_url'):
                    satellite_image_urls.append(item['thumbnail_url'])
            
            # Get cloud cover from first item
            if satellite_data[0].get('cloud_cover') is not None:
                cloud_cover = satellite_data[0]['cloud_cover']
            
            # Calculate area size from bounding box if available
            if satellite_data[0].get('bbox'):
                bbox = satellite_data[0]['bbox']
                # Simple approximation of area in square kilometers
                # This is a rough estimate and not accurate for all projections
                import math
                earth_radius = 6371  # km
                lat_diff = abs(bbox[3] - bbox[1])
                lng_diff = abs(bbox[2] - bbox[0])
                avg_lat = (bbox[1] + bbox[3]) / 2
                area_size = (
                    (math.pi / 180) * earth_radius**2 * 
                    lat_diff * lng_diff * math.cos(math.radians(avg_lat))
                )
                area_size = round(area_size)
        
        # If no satellite images found, use placeholder
        if not satellite_image_urls:
            satellite_image_urls = ['/static/placeholder.jpg']
            logger.warning("No satellite images found, using placeholder")
    except Exception as e:
        logger.error(f"Error fetching satellite data: {str(e)}")
        # Fallback to placeholder
        satellite_image_urls = ['/static/placeholder.jpg']
        cloud_cover = 10
        area_size = 100
        location_name = "Test Area"
    
    # Remove analysis results until real satellite analysis is implemented
    analysis_results = None
    
    # Initialize empty chat messages list
    chat_messages = []
    
    # Create request_params for tab navigation
    request_params = {
        'data_type': data_type,
        'start_date': start_date,
        'end_date': end_date,
        'coordinates': coordinates_str,
        'ai_analysis': ai_analysis,
        'tx_hash': tx_hash,
        'request_id': request_id
    }
    
    # Render the template with the data
    return render_template('data_results.html',
                          data_type=data_type,
                          start_date=start_date,
                          end_date=end_date,
                          coordinates=coordinates_str,
                          satellite_image_urls=satellite_image_urls,
                          cloud_cover=cloud_cover,
                          area_size=area_size,
                          location_name=location_name,
                          analysis_results=analysis_results,
                          chat_messages=chat_messages,
                          tx_hash=tx_hash,
                          request_id=request_id,
                          view=view,
                          request_params=request_params)

@app.route('/chat-message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    message = request.form.get('message', '')
    
    # Get parameters from the request
    data_type = request.form.get('data_type', 'S2MSI2A')
    start_date = request.form.get('start_date', '2023-04-15')
    end_date = request.form.get('end_date', '2023-04-22')
    coordinates_str = request.form.get('coordinates', '')
    location_name = request.form.get('location_name', 'Selected Area')
    
    # Get image URLs if available
    image_urls = request.form.getlist('image_urls[]')
    if not image_urls:
        image_urls = None
    
    try:
        # Use the AI service to generate a response
        ai_response = AIService.generate_chat_response(
            query=message,
            data_type=data_type,
            location_name=location_name,
            start_date=start_date,
            end_date=end_date,
            coordinates=coordinates_str,
            image_urls=image_urls
        )
        
        logger.info(f"Generated AI response for query: {message}")
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        ai_response = f"I'm sorry, I encountered an issue while analyzing the data. Please try again in a moment."
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'response': ai_response})
    
    # Otherwise redirect back to results page
    return redirect(url_for('data_results'))

@app.route('/download-report')
def download_report():
    """Download a report of the data"""
    # Get query parameters
    data_type = request.args.get('data_type', 'S2MSI2A')
    start_date = request.args.get('start_date', '2023-04-15')
    end_date = request.args.get('end_date', '2023-04-22')
    coordinates_str = request.args.get('coordinates', '')
    tx_hash = request.args.get('tx_hash', '')
    
    # In a real implementation, this would generate a PDF report
    # For now, just return a placeholder message
    return f"This would download a report for {data_type} data from {start_date} to {end_date} with transaction hash {tx_hash}"

@app.route('/download-image')
def download_image():
    """Download an image of the data"""
    # Get query parameters
    data_type = request.args.get('data_type', 'S2MSI2A')
    start_date = request.args.get('start_date', '2023-04-15')
    end_date = request.args.get('end_date', '2023-04-22')
    coordinates_str = request.args.get('coordinates', '')
    tx_hash = request.args.get('tx_hash', '')
    
    # In a real implementation, this would download the satellite image
    # For now, just return a placeholder message
    return f"This would download an image for {data_type} data from {start_date} to {end_date} with transaction hash {tx_hash}"

# Run the app if executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
