#!/usr/bin/env python3
"""
Debug script to show actual API response format
"""

import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the API from model
from model.traveller_map_api import TravellerMapAPI

def debug_api_response():
    """Debug actual API response format"""
    
    # Initialize API
    api = TravellerMapAPI()
    milieu = 'M1105'
    
    print("=== API RESPONSE DEBUG ===")
    
    # Test with Spinward Marches
    sector_name = "Spinward Marches"
    
    try:
        # Get sector data
        print(f"Fetching sector data for: {sector_name}")
        sector_data = api.get_sector_data(sector_name, milieu)
        
        print(f"\n=== SECTOR DATA STRUCTURE ===")
        print(f"Type: {type(sector_data)}")
        print(f"Keys: {list(sector_data.keys())}")
        
        # Show metadata
        if 'metadata' in sector_data:
            print(f"\nMETADATA:")
            print(f"  Name: {sector_data['metadata'].get('name')}")
            print(f"  Abbrev: {sector_data['metadata'].get('abbrev')}")
            print(f"  Id: {sector_data['metadata'].get('id')}")
        
        # Show systems
        if 'systems' in sector_data:
            print(f"\nSYSTEMS:")
            print(f"  Count: {len(sector_data['systems'])}")
            if sector_data['systems']:
                first_system = sector_data['systems'][0]
                print(f"  First system: {first_system}")
                print(f"  First system keys: {list(first_system.keys())}")
        
        # Show full structure
        print(f"\n=== FULL RESPONSE ===")
        print(json.dumps(sector_data, indent=2, default=str))
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_response()
