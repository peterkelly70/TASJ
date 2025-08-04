#!/usr/bin/env python3
"""
Test script to inspect what the API actually returns
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from src.api.traveller_map_api import TravellerMapAPI

def inspect_api_response():
    """Inspect actual API response for sector data"""
    
    # Initialize API
    api = TravellerMapAPI()
    milieu = os.getenv('DEFAULT_MILIEU', 'M1105')
    
    # Test with a known sector
    sector_name = "Spinward Marches"
    
    print(f"=== INSPECTING API RESPONSE FOR {sector_name} ===")
    
    try:
        # Get sector data
        sector_data = api.get_sector_data(sector_name, milieu)
        print(f"\nSECTOR DATA STRUCTURE:")
        print(f"Keys: {list(sector_data.keys())}")
        print(f"Name: {sector_data.get('name')}")
        print(f"Abbrev: {sector_data.get('abbrev')}")
        print(f"Id: {sector_data.get('id')}")
        
        # Check if systems data exists
        if 'systems' in sector_data:
            print(f"\nSYSTEMS DATA:")
            print(f"Number of systems: {len(sector_data['systems'])}")
            if sector_data['systems']:
                first_system = sector_data['systems'][0]
                print(f"First system keys: {list(first_system.keys())}")
                print(f"First system: {first_system}")
                
                # Check planets
                if 'planets' in first_system:
                    print(f"Planets in first system: {len(first_system['planets'])}")
                    if first_system['planets']:
                        first_planet = first_system['planets'][0]
                        print(f"First planet keys: {list(first_planet.keys())}")
                        print(f"First planet: {first_planet}")
        
        # Check if sector has systems in different format
        print(f"\nFULL SECTOR DATA:")
        for key, value in sector_data.items():
            if isinstance(value, list):
                print(f"{key}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"{key}: dict with {len(value)} keys")
            else:
                print(f"{key}: {value}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_api_response()
