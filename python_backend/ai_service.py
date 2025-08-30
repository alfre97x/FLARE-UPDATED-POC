"""
AI Service for SpaceData application
Handles OpenAI API integration for various AI features
"""

import os
import json
import logging
import base64
import requests
from typing import List, Dict, Any, Optional, Tuple
import openai
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
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
file_handler = logging.FileHandler('ai_service.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('AI_API_KEY')
OPENAI_API_URL = os.getenv('AI_API_URL', 'https://api.openai.com/v1/chat/completions')

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# User agent for geocoding
USER_AGENT = "SpaceData-App/1.0"

class AIService:
    """Service for AI-related functionality"""
    
    @staticmethod
    def generate_chat_response(
        query: str,
        data_type: str,
        location_name: str,
        start_date: str,
        end_date: str,
        coordinates: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> str:
        """
        Generate a response for the chat assistant in the data results screen
        
        Args:
            query: The user's query
            data_type: The type of satellite data
            location_name: The name of the location
            start_date: The start date of the data
            end_date: The end date of the data
            coordinates: Optional coordinates string in JSON format
            image_urls: Optional list of URLs to satellite images
            
        Returns:
            The AI-generated response
        """
        try:
            # Map data type codes to human-readable names
            data_type_names = {
                'S2MSI2A': 'Sentinel-2 Level 2A (multispectral imagery)',
                'S1GRD': 'Sentinel-1 SAR (radar imagery)',
                'S3OLCI': 'Sentinel-3 OLCI (ocean and land color)'
            }
            
            # Get human-readable data type
            data_type_name = data_type_names.get(data_type, data_type)
            
            # Process coordinates if provided
            polygon_info = ""
            if coordinates:
                try:
                    # Parse the coordinates JSON string
                    coords_list = json.loads(coordinates)
                    
                    if coords_list and len(coords_list) >= 3:
                        # Calculate center of polygon
                        lats = [point[0] for point in coords_list]
                        lngs = [point[1] for point in coords_list]
                        
                        center_lat = sum(lats) / len(lats)
                        center_lng = sum(lngs) / len(lngs)
                        
                        # Format polygon for prompt
                        polygon_str = ", ".join([f"[{lat}, {lng}]" for lat, lng in coords_list])
                        polygon_info = f"""
                        The area being analyzed is defined by the following polygon coordinates:
                        {polygon_str}
                        
                        The center of this area is approximately at coordinates [{center_lat:.4f}, {center_lng:.4f}].
                        """
                        
                        # Try to get nearby cities/locations for context
                        try:
                            geolocator = Nominatim(user_agent=USER_AGENT)
                            location = geolocator.reverse(f"{center_lat}, {center_lng}", language='en')
                            
                            if location and location.address:
                                polygon_info += f"\nThis area is located near or within: {location.address}"
                        except Exception as geo_error:
                            logger.warning(f"Geocoding error: {str(geo_error)}")
                except Exception as coord_error:
                    logger.warning(f"Error processing coordinates: {str(coord_error)}")
            
            # Process image URLs if provided
            image_info = ""
            if image_urls and len(image_urls) > 0:
                image_info = f"You have access to {len(image_urls)} satellite images for this area."
            
            # Create system prompt for chat assistant
            system_prompt = f"""
            You are an AI assistant for SpaceData, a platform that provides satellite imagery and analysis.
            You are currently helping a user analyze {data_type_name} satellite data for {location_name} from {start_date} to {end_date}.
            
            {polygon_info}
            {image_info}
            
            Your role is to provide expert insights and answer questions about the satellite data and the geographic area.
            Be concise, informative, and scientifically accurate. Focus on providing valuable information about:
            - Land cover and land use in the area
            - Environmental changes and trends
            - Geographic and ecological context
            - Potential applications of this satellite data
            
            If you don't know the answer to a specific question, acknowledge that and suggest what information might be helpful.
            
            Keep responses under 200 words unless the user specifically asks for more detailed information.
            """
            
            # Create messages for the API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract and return the response text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            # Fallback response
            return f"I'm sorry, I encountered an issue while analyzing the satellite data for {location_name}. The system is still processing your request. Please try again in a moment, or ask a different question about the data or the region."
    
    @staticmethod
    def generate_home_assistant_response(query: str) -> str:
        """
        Generate a response for the home page AI assistant
        
        Args:
            query: The user's query
            
        Returns:
            The AI-generated response
        """
        try:
            # Create system prompt for home assistant
            system_prompt = """
            You are an AI assistant for SpaceData, a platform that provides satellite imagery and analysis.
            Your role is to help users understand how to use the platform and guide them to connect their wallet
            and explore the available services.
            
            Be concise, helpful, and encouraging. Focus on explaining how the platform works and guiding users
            to take the next steps (connecting wallet and exploring services).
            
            Key features to highlight:
            - Users can connect their Flare wallet to pay for satellite data
            - The platform offers urban monitoring, agricultural insights, and coastal monitoring
            - Users can select specific areas on a map and date ranges for satellite imagery
            - AI analysis is available to provide insights on the satellite data
            
            Keep responses under 150 words.
            """
            
            # Create messages for the API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            # Extract and return the response text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating home assistant response: {str(e)}")
            # Fallback response
            return "I'm here to help you use SpaceData! You can connect your wallet using the button below, then explore our satellite data services. If you have specific questions about our urban monitoring, agricultural insights, or coastal monitoring services, feel free to ask."
    
    @staticmethod
    def geocode_location(location_query: str) -> Tuple[Optional[List[List[float]]], Optional[str]]:
        """
        Convert a location description to coordinates and generate a polygon
        
        Args:
            location_query: The location description (e.g., "Paris, France")
            
        Returns:
            A tuple containing:
            - A list of [lat, lng] coordinates forming a polygon around the location, or None if geocoding failed
            - The formatted location name, or None if geocoding failed
        """
        try:
            # Initialize geocoder
            geolocator = Nominatim(user_agent=USER_AGENT)
            
            # Geocode the location
            location = geolocator.geocode(location_query, exactly_one=True)
            
            if not location:
                logger.warning(f"Location not found: {location_query}")
                return None, None
            
            # Get the coordinates
            lat, lng = location.latitude, location.longitude
            
            # Create a bounding box around the location
            # Size depends on the type of location (city, country, etc.)
            # This is a simple implementation - could be improved with more context
            
            # Check if we have a bounding box in the raw data
            if hasattr(location, 'raw') and 'boundingbox' in location.raw:
                try:
                    # Extract bounding box from raw data
                    bbox = location.raw['boundingbox']
                    min_lat, max_lat, min_lng, max_lng = map(float, bbox)
                    
                    # Create polygon from bounding box
                    polygon = [
                        [min_lat, min_lng],
                        [min_lat, max_lng],
                        [max_lat, max_lng],
                        [max_lat, min_lng]
                    ]
                    
                    return polygon, location.address
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error extracting bounding box: {str(e)}")
                    # Fall through to default polygon creation
            
            # Default polygon creation - create a box around the point
            # Size depends on the type of location (approximated by address length)
            address_length = len(location.address) if hasattr(location, 'address') else 20
            
            # Smaller delta for longer addresses (likely more specific locations)
            delta = max(0.01, min(0.2, 0.5 / (address_length / 20)))
            
            # Create polygon
            polygon = [
                [lat - delta, lng - delta],
                [lat - delta, lng + delta],
                [lat + delta, lng + delta],
                [lat + delta, lng - delta]
            ]
            
            return polygon, location.address
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding service error: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Error geocoding location: {str(e)}")
            return None, None
    
    @staticmethod
    def analyze_satellite_data(
        data_type: str,
        location_name: str,
        start_date: str,
        end_date: str,
        image_urls: List[str],
        coordinates: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze satellite data and generate insights
        
        Args:
            data_type: The type of satellite data (e.g., 'S2MSI2A')
            location_name: The name of the location
            start_date: The start date of the data
            end_date: The end date of the data
            image_urls: List of URLs to satellite images
            coordinates: Optional coordinates string in JSON format
            
        Returns:
            A dictionary containing analysis results
        """
        # Map data type codes to human-readable names
        data_type_names = {
            'S2MSI2A': 'Sentinel-2 Level 2A (multispectral imagery)',
            'S1GRD': 'Sentinel-1 SAR (radar imagery)',
            'S3OLCI': 'Sentinel-3 OLCI (ocean and land color)'
        }
        
        # Get human-readable data type
        data_type_name = data_type_names.get(data_type, data_type)
        
        # Default analysis results in case all approaches fail
        default_results = {
            "land_cover": {
                "forest": 33.3,
                "urban": 33.3,
                "water": 33.4
            },
            "change": {
                "forest_change": 0.0,
                "urban_change": 0.0,
                "water_change": 0.0
            },
            "insights": [
                f"Analysis for {location_name} from {start_date} to {end_date}.",
                "No detailed analysis available. Please try again later.",
                "The system is still processing your request."
            ]
        }
        
        # Parse coordinates if provided
        polygon_info = ""
        nearest_cities = []
        is_water_body = False
        water_body_name = None
        
        try:
            if coordinates:
                # Parse the coordinates JSON string
                coords_list = json.loads(coordinates)
                
                if coords_list and len(coords_list) >= 3:
                    # Calculate center of polygon
                    lats = [point[0] for point in coords_list]
                    lngs = [point[1] for point in coords_list]
                    
                    center_lat = sum(lats) / len(lats)
                    center_lng = sum(lngs) / len(lngs)
                    
                    # Format polygon for prompt
                    polygon_str = ", ".join([f"[{lat}, {lng}]" for lat, lng in coords_list])
                    polygon_info = f"""
                    The area being analyzed is defined by the following polygon coordinates:
                    {polygon_str}
                    
                    The center of this area is approximately at coordinates [{center_lat:.4f}, {center_lng:.4f}].
                    """
                    
                    # Log the polygon information for debugging
                    logger.info(f"Generated polygon information for coordinates: {polygon_info}")
                    
                    # Try to get nearby cities/locations for context
                    try:
                        geolocator = Nominatim(user_agent=USER_AGENT)
                        location = geolocator.reverse(f"{center_lat}, {center_lng}", language='en')
                        
                        # Check if this is a water body (sea, ocean, etc.)
                        if location and location.address:
                            address_lower = location.address.lower()
                            water_body_keywords = ['sea', 'ocean', 'gulf', 'bay', 'strait', 'channel', 'mediterranean', 'atlantic', 'pacific', 'indian ocean', 'arctic']
                            
                            # Check if any water body keyword is in the address
                            for keyword in water_body_keywords:
                                if keyword in address_lower:
                                    is_water_body = True
                                    water_body_name = location.address
                                    logger.info(f"Detected water body: {water_body_name}")
                                    break
                            
                            polygon_info += f"\nThis area is located near or within: {location.address}"
                            
                            # Try to get additional nearby locations for more context
                            water_body_count = 0
                            land_count = 0
                            
                            for i, point in enumerate(coords_list):
                                if i % 2 == 0:  # Only check every other point to avoid too many API calls
                                    try:
                                        loc = geolocator.reverse(f"{point[0]}, {point[1]}", language='en')
                                        if loc and loc.address:
                                            # Check if this point is also a water body
                                            loc_address_lower = loc.address.lower()
                                            is_point_water = any(keyword in loc_address_lower for keyword in water_body_keywords)
                                            
                                            if is_point_water:
                                                water_body_count += 1
                                            else:
                                                land_count += 1
                                                
                                            if loc.address != location.address:
                                                nearest_cities.append(loc.address)
                                    except Exception:
                                        pass
                            
                            # If most points are water, mark as water body
                            if water_body_count > land_count and water_body_count > 0:
                                is_water_body = True
                                logger.info(f"Majority of points ({water_body_count}/{water_body_count + land_count}) are in water bodies")
                            
                            if nearest_cities:
                                polygon_info += f"\nNearby areas include: {', '.join(nearest_cities[:3])}"
                                
                            # Add water body information to polygon info if detected
                            if is_water_body:
                                polygon_info += f"\n\nIMPORTANT: This area appears to be primarily a water body ({water_body_name if water_body_name else 'sea or ocean'})."
                    except Exception as geo_error:
                        logger.warning(f"Geocoding error: {str(geo_error)}")
        except Exception as coord_error:
            logger.warning(f"Error processing coordinates: {str(coord_error)}")
        
        # Try to analyze the data using the coordinates
        try:
            if polygon_info:
                # Create a geography-focused prompt
                fallback_prompt = f"""
                You are an expert in geographic analysis and Earth observation.
                
                {polygon_info}
                
                Based ONLY on the geographic location information provided (without satellite imagery),
                generate an educated estimate of the land cover and recent changes for this area.
                
                Use your knowledge of world geography, typical land use patterns, and regional characteristics
                to make your best estimate for the area described.
                
                The analysis should cover the period from {start_date} to {end_date}.
                
                IMPORTANT REQUIREMENTS:
                - Land cover percentages MUST sum to exactly 100%
                - Forest percentage should be between 10-70% depending on the location
                - Urban percentage should be between 10-60% depending on the location
                - Water percentage should be between 5-50% depending on the location
                - Change percentages should be small, realistic values between -5% and +5%
                
                Return your response as a JSON object with the following structure:
                {{
                    "land_cover": {{
                        "forest": float,  // percentage (0-100)
                        "urban": float,   // percentage (0-100)
                        "water": float    // percentage (0-100)
                    }},
                    "change": {{
                        "forest_change": float,  // percentage change (-5 to 5)
                        "urban_change": float,   // percentage change (-5 to 5)
                        "water_change": float    // percentage change (-5 to 5)
                    }},
                    "insights": [
                        string,  // 3-5 key insights about the region based on geographic knowledge
                        ...
                    ]
                }}
                """
                
                # Create messages for the fallback API call
                fallback_messages = [
                    {"role": "system", "content": fallback_prompt},
                    {"role": "user", "content": f"Please provide a geographic analysis for the area described."}
                ]
                
                # Call OpenAI API with fallback prompt
                try:
                    fallback_response = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=fallback_messages,
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    # Extract the response text
                    fallback_text = fallback_response.choices[0].message.content.strip()
                    
                    # Parse the JSON response
                    try:
                        # Find JSON in the response (in case there's additional text)
                        json_start = fallback_text.find('{')
                        json_end = fallback_text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = fallback_text[json_start:json_end]
                            analysis_results = json.loads(json_str)
                        else:
                            # If no JSON found, use the whole response
                            analysis_results = json.loads(fallback_text)
                        
                        # Validate the structure
                        if all(key in analysis_results for key in ['land_cover', 'change', 'insights']):
                            logger.info("Successfully generated fallback analysis using geographic information directly")
                            
                            # Add a note that this is a fallback analysis
                            if 'insights' in analysis_results and isinstance(analysis_results['insights'], list):
                                analysis_results['insights'].append(
                                    "Note: This analysis is based on geographic information only, not satellite imagery."
                                )
                            
                            return analysis_results
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Error parsing fallback analysis results: {str(e)}")
                except Exception as api_error:
                    logger.error(f"Error calling OpenAI API for fallback analysis: {str(api_error)}")
        except Exception as analysis_error:
            logger.error(f"Error in fallback analysis: {str(analysis_error)}")
        
        # Return default results if all approaches fail
        logger.warning("All analysis approaches failed, returning default results")
        return default_results
