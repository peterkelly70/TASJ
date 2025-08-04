#!/usr/bin/env python3
"""
Detailed inspection of API response structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.traveller_map_api import TravellerMapAPI
from dotenv import load_dotenv
import json

load_dotenv()

api = TravellerMapAPI()
milieu = os.getenv('DEFAULT_MILIEU', 'M1105')

# Test with a sector that should have data
sector_name = 'Spinward Marches'
print(f"=== INSPECTING API RESPONSE FOR {sector_name} ===")

try:
    # Get sector data
    data = api.get_sector_data(sector_name, milieu)
    
    print(f"Response type: {type(data)}")
    print(f"Keys in response: {list(data.keys())}")
    
    # Check all keys and their content
    for key, value in data.items():
        if isinstance(value, list):
            print(f"{key}: list with {len(value)} items")
            if len(value) > 0 and isinstance(value[0], dict):
                print(f"  First item keys: {list(value[0].keys())}")
        elif isinstance(value, dict):
            print(f"{key}: dict with {len(value)} keys")
            if len(value) > 0:
                print(f"  Keys: {list(value.keys())}")
        else:
            print(f"{key}: {type(value)} - {value}")
    
    # Focus on Worlds data
    worlds = data.get('Worlds', [])
    print(f"\n=== WORLDS DATA ===")
    print(f"Worlds count: {len(worlds)}")
    
    if worlds:
        print(f"First world type: {type(worlds[0])}")
        if isinstance(worlds[0], dict):
            print("First world structure:")
            for k, v in worlds[0].items():
                print(f"  {k}: {v}")
    
    # Check if there's a different field name
    print(f"\n=== CHECKING FOR SYSTEM DATA ===")
    # Try different possible field names
    possible_fields = ['Worlds', 'worlds', 'Systems', 'systems', 'planets', 'data']
    for field in possible_fields:
        if field in data:
            items = data[field]
            print(f"{field}: {len(items)} items")
            if items and isinstance(items[0], dict):
                print(f"  Sample keys: {list(items[0].keys())}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
