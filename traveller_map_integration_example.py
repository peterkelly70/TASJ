#!/usr/bin/env python3
"""
Traveller Map Integration Example

This script demonstrates how to use the TravellerMapAPI and TravellerMapDataMapper
classes to fetch and map data from the Traveller Map API into the application.
"""

import os
import sys
import json
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from model.traveller_map_api_fixed_v2 import TravellerMapAPI
from model.traveller_map_data_mapper import TravellerMapDataMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_json(data, filename):
    """Save data as JSON to the specified file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved data to {filename}")

def main():
    """Main entry point for the integration example."""
    print("=== TRAVELLER MAP INTEGRATION EXAMPLE ===")
    
    # Need QApplication for QPixmap
    qt_app = QApplication.instance() or QApplication(sys.argv)
    
    # Create API client and data mapper
    api = TravellerMapAPI()
    mapper = TravellerMapDataMapper(api)
    
    # Example 1: Fetch and map sector data
    print("\n1. Fetching and mapping sector data...")
    sector_name = "Spinward Marches"
    mapped_sector = mapper.fetch_and_map_sector(sector_name)
    
    if mapped_sector:
        print(f"✓ Successfully mapped sector: {mapped_sector['name']}")
        print(f"  - Found {len(mapped_sector['systems'])} systems")
        print(f"  - Found {len(mapped_sector['subsectors'])} subsectors")
        
        # Save sector data to JSON for inspection
        save_json(
            {k: v for k, v in mapped_sector.items() if k != 'image'},
            "database/content/json/sector_data.json"
        )
        
        # Check if sector image was retrieved
        if mapped_sector['image']:
            print(f"✓ Successfully retrieved sector image")
            print(f"  - Image size: {mapped_sector['image'].width()}x{mapped_sector['image'].height()}")
            print(f"  - Saved to: {mapped_sector['image_path']}")
        else:
            print("✗ Failed to retrieve sector image")
            
        # Example 2: Extract a specific system from the sector data
        print("\n2. Extracting system data from sector...")
        system_hex = "1910"  # Regina
        system = next((s for s in mapped_sector['systems'] if s['hex'] == system_hex), None)
        
        if system:
            print(f"✓ Found system: {system['name']} ({system['hex']})")
            print(f"  - UWP: {system['uwp']}")
            print(f"  - Starport: {system['starport']}")
            print(f"  - Tech Level: {system['tech_level']}")
            
            # Save system data to JSON for inspection
            save_json(system, "database/content/json/system_data.json")
        else:
            print(f"✗ System {system_hex} not found in sector {sector_name}")
    else:
        print(f"✗ Failed to map sector {sector_name}")
    
    # Example 3: Fetch and map a specific system directly
    print("\n3. Fetching and mapping system data directly...")
    mapped_system = mapper.fetch_and_map_system(sector_name, system_hex)
    
    if mapped_system:
        print(f"✓ Successfully mapped system: {mapped_system['name']} ({mapped_system['hex']})")
        print(f"  - UWP: {mapped_system['uwp']}")
        print(f"  - Starport: {mapped_system['starport']}")
        print(f"  - Tech Level: {mapped_system['tech_level']}")
        
        # Check if system image was retrieved
        if mapped_system['image']:
            print(f"✓ Successfully retrieved system image")
            print(f"  - Image size: {mapped_system['image'].width()}x{mapped_system['image'].height()}")
            print(f"  - Saved to: {mapped_system['image_path']}")
        else:
            print("✗ Failed to retrieve system image")
    else:
        print(f"✗ Failed to map system {system_hex} in sector {sector_name}")
    
    # Example 4: Search for systems
    print("\n4. Searching for systems...")
    search_term = "Regina"
    search_results = mapper.search_and_map_results(search_term)
    
    if search_results:
        print(f"✓ Successfully searched for '{search_term}'")
        print(f"  - Found {len(search_results)} results")
        
        # Print search results
        for i, result in enumerate(search_results):
            result_type = result.get('type', 'Unknown')
            name = result.get('name', 'Unknown')
            sector = result.get('sector', 'Unknown')
            hex_code = result.get('hex', '')
            uwp = result.get('uwp', '')
            
            print(f"  - Result {i+1}: {name} ({result_type}) in {sector} {hex_code} {uwp}")
            
        # Save search results to JSON for inspection
        save_json(search_results, "database/content/json/search_results.json")
    else:
        print(f"✗ No search results found for '{search_term}'")
    
    # Example 5: Get available milieux
    print("\n5. Getting available milieux...")
    milieux = mapper.get_available_milieux()
    
    if milieux:
        print(f"✓ Successfully retrieved milieux")
        print(f"  - Found {len(milieux)} milieux")
        
        # Print milieux
        for milieu in milieux:
            default_marker = " (default)" if milieu.get("is_default", False) else ""
            print(f"  - {milieu.get('code', 'Unknown')}: {milieu.get('name', '')}{default_marker}")
            
        # Save milieux to JSON for inspection
        save_json(milieux, "database/content/json/milieux.json")
    else:
        print(f"✗ Failed to retrieve milieux")
    
    print("\n=== INTEGRATION EXAMPLE COMPLETED ===")
    print("JSON data files have been saved to the database/content/json directory for inspection.")

if __name__ == "__main__":
    main()
