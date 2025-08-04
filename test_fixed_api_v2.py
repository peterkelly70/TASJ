#!/usr/bin/env python3
"""
Test script for the fixed Traveller Map API client v2.
This script tests all the key functionality of the updated API client.
"""

import os
import sys
import json
import logging
from PyQt6.QtWidgets import QApplication
from model.traveller_map_api_fixed_v2 import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api():
    """Test the fixed Traveller Map API client v2."""
    print("=== TESTING FIXED TRAVELLER MAP API CLIENT V2 ===")
    
    # Need QApplication for QPixmap
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create API instance
    api = TravellerMapAPI()
    
    # Test sector data retrieval
    sector_name = "Spinward Marches"
    print(f"\n1. Testing sector data retrieval for '{sector_name}'...")
    try:
        sector_data = api.get_sector_data(sector_name)
        print("✓ Successfully retrieved sector data")
        print(f"  - Metadata keys: {list(sector_data['metadata'].keys() if sector_data['metadata'] else [])}")
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
            print("✓ Successfully retrieved sector image")
            print(f"  - Image size: {pixmap.width()}x{pixmap.height()} pixels")
            
            # Save the image
            save_path = api.save_sector_image(sector_name)
            if save_path:
                print(f"  - Saved to: {save_path}")
            else:
                print("✗ Failed to save sector image")
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
            print("✓ Successfully retrieved system image")
            print(f"  - Image size: {pixmap.width()}x{pixmap.height()} pixels")
            
            # Save the image
            save_path = api.save_system_image(sector_name, system_hex)
            if save_path:
                print(f"  - Saved to: {save_path}")
            else:
                print("✗ Failed to save system image")
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
            if search_results["Results"]["Items"]:
                first_result = search_results["Results"]["Items"][0]
                name = first_result.get('Name', first_result.get('Text', 'Unknown'))
                sector = first_result.get('Sector', first_result.get('SectorName', 'Unknown'))
                hex_code = first_result.get('Hex', first_result.get('HexCode', 'Unknown'))
                print(f"  - First result: {name} in {sector} ({hex_code})")
            else:
                print("  - No result items found")
        else:
            print(f"✗ No results found for '{search_term}'")
    except Exception as e:
        print(f"✗ Error searching: {e}")
    
    # Test milieu functionality
    print("\n5. Testing milieu functionality...")
    try:
        milieux = api.get_available_milieux()
        if milieux:
            print("✓ Successfully retrieved available milieux")
            print(f"  - Found {len(milieux)} milieux")
            
            # Print available milieux
            for milieu in milieux:
                default_marker = " (default)" if milieu.get("IsDefault", False) else ""
                print(f"  - {milieu.get('Code', 'Unknown')}: {milieu.get('Name', '')}{default_marker}")
        else:
            print("✗ Failed to retrieve milieux or none available")
    except Exception as e:
        print(f"✗ Error retrieving milieux: {e}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_api()
