#!/usr/bin/env python3
"""
Test script for the Traveller Map Data Mapper.
This script tests the data mapper's ability to fetch and map data from the API.
"""

import os
import sys
import json
import logging
from PyQt6.QtWidgets import QApplication
from model.traveller_map_data_mapper import TravellerMapDataMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_mapper():
    """Test the Traveller Map Data Mapper."""
    print("=== TESTING TRAVELLER MAP DATA MAPPER ===")
    
    # Need QApplication for QPixmap
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create mapper
    mapper = TravellerMapDataMapper()
    
    # Test sector mapping
    sector_name = "Spinward Marches"
    print(f"\n1. Testing sector mapping for '{sector_name}'...")
    try:
        mapped_sector = mapper.fetch_and_map_sector(sector_name)
        if mapped_sector:
            print("✓ Successfully mapped sector data")
            print(f"  - Sector name: {mapped_sector['name']}")
            print(f"  - Sector abbreviation: {mapped_sector['abbreviation']}")
            print(f"  - Sector coordinates: ({mapped_sector['x']}, {mapped_sector['y']})")
            print(f"  - Found {len(mapped_sector['systems'])} systems")
            print(f"  - Found {len(mapped_sector['subsectors'])} subsectors")
            
            # Check if sector image was retrieved
            if mapped_sector['image']:
                print("✓ Successfully mapped sector image")
                print(f"  - Image size: {mapped_sector['image'].width()}x{mapped_sector['image'].height()}")
                print(f"  - Saved to: {mapped_sector['image_path']}")
            else:
                print("✗ Failed to map sector image")
        else:
            print("✗ Failed to map sector data")
    except Exception as e:
        print(f"✗ Error mapping sector data: {e}")
    
    # Test system mapping
    system_hex = "1910"  # Regina
    print(f"\n2. Testing system mapping for '{sector_name}' hex '{system_hex}'...")
    try:
        mapped_system = mapper.fetch_and_map_system(sector_name, system_hex)
        if mapped_system:
            print("✓ Successfully mapped system data")
            print(f"  - System name: {mapped_system['name']}")
            print(f"  - System hex: {mapped_system['hex']}")
            print(f"  - UWP: {mapped_system['uwp']}")
            print(f"  - Starport: {mapped_system['starport']}")
            print(f"  - Tech level: {mapped_system['tech_level']}")
            
            # Check if system image was retrieved
            if mapped_system['image']:
                print("✓ Successfully mapped system image")
                print(f"  - Image size: {mapped_system['image'].width()}x{mapped_system['image'].height()}")
                print(f"  - Saved to: {mapped_system['image_path']}")
            else:
                print("✗ Failed to map system image")
        else:
            print("✗ Failed to map system data")
    except Exception as e:
        print(f"✗ Error mapping system data: {e}")
    
    # Test search mapping
    search_term = "Regina"
    print(f"\n3. Testing search mapping for '{search_term}'...")
    try:
        mapped_results = mapper.search_and_map_results(search_term)
        if mapped_results:
            print("✓ Successfully mapped search results")
            print(f"  - Found {len(mapped_results)} results")
            
            # Print first result
            if mapped_results:
                first_result = mapped_results[0]
                print(f"  - First result: {first_result['name']} in {first_result['sector']} ({first_result['hex']})")
                print(f"  - UWP: {first_result.get('uwp', 'N/A')}")
        else:
            print("✗ No search results found or mapping failed")
    except Exception as e:
        print(f"✗ Error mapping search results: {e}")
    
    # Test milieu mapping
    print("\n4. Testing milieu mapping...")
    try:
        mapped_milieux = mapper.get_available_milieux()
        if mapped_milieux:
            print("✓ Successfully mapped milieux")
            print(f"  - Found {len(mapped_milieux)} milieux")
            
            # Print available milieux
            for milieu in mapped_milieux:
                default_marker = " (default)" if milieu.get("is_default", False) else ""
                print(f"  - {milieu.get('code', 'Unknown')}: {milieu.get('name', '')}{default_marker}")
        else:
            print("✗ Failed to map milieux")
    except Exception as e:
        print(f"✗ Error mapping milieux: {e}")
    
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_data_mapper()
