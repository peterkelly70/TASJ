#!/usr/bin/env python3
"""
Debug script for the Traveller Map API image endpoints.
This script tests the image endpoints and saves the raw data for inspection.
"""

import os
import sys
import logging
import requests
from model.traveller_map_api_fixed_v2 import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_image_endpoints():
    """Debug the image endpoints of the Traveller Map API."""
    print("=== DEBUGGING TRAVELLER MAP API IMAGE ENDPOINTS ===")
    
    # Create API instance
    api = TravellerMapAPI()
    
    # Test direct URL access to poster endpoint
    sector_name = "Spinward Marches"
    print(f"\n1. Testing direct URL access to poster endpoint for '{sector_name}'...")
    try:
        # Construct the URL manually
        url = f"{api.api_base_url}/poster?sector={sector_name}&type=png&scale=64&milieu={api.milieu}"
        print(f"   URL: {url}")
        
        # Make the request directly
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        print(f"   Content-Type: {content_type}")
        print(f"   Content Length: {len(response.content)} bytes")
        
        # Save the raw data
        output_dir = "debug_output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{sector_name.replace(' ', '_')}_direct.png")
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"   Saved raw data to: {output_path}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test API client poster endpoint
    print(f"\n2. Testing API client poster endpoint for '{sector_name}'...")
    try:
        # Get image data using the API client
        options = {"type": "png", "scale": "64"}
        image_data = api.get_sector_image(sector_name, options=options)
        
        if image_data:
            print(f"   Received {len(image_data)} bytes of data")
            
            # Save the raw data
            output_path = os.path.join(output_dir, f"{sector_name.replace(' ', '_')}_api.png")
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"   Saved raw data to: {output_path}")
        else:
            print("   No image data received")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test jumpmap endpoint for a system
    system_hex = "1910"  # Regina
    print(f"\n3. Testing jumpmap endpoint for '{sector_name}' hex '{system_hex}'...")
    try:
        # Construct the URL manually
        url = f"{api.api_base_url}/jumpmap?sector={sector_name}&hex={system_hex}&type=png&scale=64&milieu={api.milieu}"
        print(f"   URL: {url}")
        
        # Make the request directly
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        print(f"   Content-Type: {content_type}")
        print(f"   Content Length: {len(response.content)} bytes")
        
        # Save the raw data
        output_path = os.path.join(output_dir, f"{sector_name.replace(' ', '_')}_{system_hex}_direct.png")
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"   Saved raw data to: {output_path}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test API client jumpmap endpoint
    print(f"\n4. Testing API client jumpmap endpoint for '{sector_name}' hex '{system_hex}'...")
    try:
        # Get image data using the API client
        options = {"type": "png", "scale": "64"}
        image_data = api.get_system_image(sector_name, system_hex, options=options)
        
        if image_data:
            print(f"   Received {len(image_data)} bytes of data")
            
            # Save the raw data
            output_path = os.path.join(output_dir, f"{sector_name.replace(' ', '_')}_{system_hex}_api.png")
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"   Saved raw data to: {output_path}")
        else:
            print("   No image data received")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== DEBUG COMPLETED ===")

if __name__ == "__main__":
    debug_image_endpoints()
