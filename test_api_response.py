#!/usr/bin/env python3
"""
Test script to inspect actual API response format
"""

import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_api_response():
    """Test what API returns for sector data"""
    
    # Import the API module directly
    try:
        from api.traveller_map_api import TravellerMapAPI
    except ImportError:
        try:
            from src.api.traveller_map_api import TravellerMapAPI
        except ImportError:
            # Try direct import
            exec(open('api/traveller_map_api.py').read(), globals())
            TravellerMapAPI = globals()['TravellerMapAPI']
    
    # Initialize API
    api = TravellerMapAPI()
    milieu = 'M1105'
    
    print("=== API RESPONSE INSPECTION ===")
    
    # Test with Spinward Marches
    sector_name = "Spinward Marches"
    
    try:
        # Get sector data
        sector_data = api.get_sector_data(sector_name, milieu)
        
        print(f"\n=== SECTOR DATA FOR {sector_name} ===")
        print(f"Type: {type(sector_data)}")
        print(f"Keys: {list(sector_data.keys())}")
        
        # Show all data
        print(f"\n=== FULL SECTOR DATA ===")
        print(json.dumps(sector_data, indent=2, default=str))
        
        # Check for systems
        if isinstance(sector_data, dict):
            for key, value in sector_data.items():
                if isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    if len(value) > 0:
                        print(f"  First item type: {type(value[0])}")
                        if isinstance(value[0], dict):
                            print(f"  First item keys: {list(value[0].keys())}")
                elif isinstance(value, dict):
                    print(f"{key}: dict with {len(value)} keys")
                else:
                    print(f"{key}: {value}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_response()
