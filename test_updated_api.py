#!/usr/bin/env python3
"""
Test script for the updated Traveller Map API client.
This script tests all the key functionality of the updated API client.
"""

import os
import sys
import json
import logging
from PyQt6.QtWidgets import QApplication
from model.traveller_map_api_updated import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api():
    """Test the updated Traveller Map API client."""
    print("=== TESTING UPDATED TRAVELLER MAP API CLIENT ===")
    
    # Create API instance
    api = TravellerMapAPI()
    
    # Test sector data retrieval
    sector_name = "Spinward Marches"
    print(f"\n1. Testing sector data retrieval for '{sector_name}'...")
    try:
        sector_data = api.get_sector_data(sector_name)
        print(f"✓ Successfully retrieved sector data")
        print(f"  - Metadata keys: {list(sector_data['metadata'].keys())}")
        print(f"  - Found {len(sector_data['systems'])} systems")
        
        # Print first system as example
        if sector_data['systems']:
            first_system = sector_data['systems'][0]
            print(f"  - First system: {first_system['hex']} {first_system['name']} {first_system.get('uwp', '')}")
    except Exception as e:
        print(f"✗ Error retrieving sector data: {e}")
    
    # Test sector image retrieval
    print(f"\n2. Testing sector image retrieval for '{sector_name}'...")
    try:
        # Need QApplication for QPixmap
        app = QApplication.instance() or QApplication(sys.argv)
        
        pixmap, error = api.get_sector_pixmap(sector_name)
        if pixmap and not error:
            print(f"✓ Successfully retrieved sector image")
            print(f"  - Image size: {pixmap.width()}x{pixmap.height()} pixels")
            
            # Save the image
            save_path = api.save_sector_image(sector_name)
            print(f"  - Saved to: {save_path}")
        else:
            print(f"✗ Error retrieving sector image: {error}")
    except Exception as e:
        print(f"✗ Error retrieving sector image: {e}")
    
    # Test system image retrieval
    system_hex = "1910"  # Regina
    print(f"\n3. Testing system image retrieval for '{sector_name}' hex '{system_hex}'...")
    try:
        pixmap, error = api.get_system_pixmap(sector_name, system_hex)
        if pixmap and not error:
            print(f"✓ Successfully retrieved system image")
            print(f"  - Image size: {pixmap.width()}x{pixmap.height()} pixels")
            
            # Save the image
            save_path = api.save_system_image(sector_name, system_hex)
            print(f"  - Saved to: {save_path}")
        else:
            print(f"✗ Error retrieving system image: {error}")
    except Exception as e:
        print(f"✗ Error retrieving system image: {e}")
    
    # Test search functionality
    search_term = "Regina"
    print(f"\n4. Testing search for '{search_term}'...")
    try:
        search_results = api.search(search_term)
        if "Results" in search_results and search_results["Results"]["Count"] > 0:
            print(f"✓ Successfully searched for '{search_term}'")
            print(f"  - Found {search_results['Results']['Count']} results")
            
            # Print first result
            first_result = search_results["Results"]["Items"][0]
            # The structure might vary, so let's be defensive
            name = first_result.get('Name', first_result.get('Text', 'Unknown'))
            sector = first_result.get('Sector', first_result.get('SectorName', 'Unknown'))
            hex_code = first_result.get('Hex', first_result.get('HexCode', 'Unknown'))
            print(f"  - First result: {name} in {sector} ({hex_code})")
        else:
            print(f"✗ No results found for '{search_term}'")
    except Exception as e:
        print(f"✗ Error searching: {e}")
    
    # Test milieu functionality
    print(f"\n5. Testing milieu functionality...")
    try:
        milieux = api.get_available_milieux()
        print(f"✓ Successfully retrieved available milieux")
        print(f"  - Found {len(milieux)} milieux")
        
        # Print available milieux
        for milieu in milieux:
            default_marker = " (default)" if milieu.get("IsDefault", False) else ""
            print(f"  - {milieu['Code']}: {milieu.get('Name', '')}{default_marker}")
    except Exception as e:
        print(f"✗ Error retrieving milieux: {e}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_api()
