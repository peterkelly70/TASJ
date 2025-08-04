#!/usr/bin/env python3
"""
Debug script to check what data is being passed to systems table
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_map_api import TravellerMapAPI
from model.traveller_database import TravellerDatabase

def debug_population():
    """Debug what data is being passed to systems table"""
    print("=== DEBUG: System Population Data ===")
    
    api = TravellerMapAPI()
    db = TravellerDatabase()
    
    # Get current systems table columns
    columns = db.get_table_columns('systems')
    print("Systems table columns:", columns)
    
    # Fetch T5 data for a sector
    sector_name = "Spinward Marches"
    t5_data = api.get_sector_t5(sector_name)
    
    # Parse systems
    systems = api._parse_t5_systems(t5_data)
    print(f"Found {len(systems)} systems")
    
    # Show first few systems and their data
    for i, system in enumerate(systems[:3]):
        print(f"\nSystem {i+1}:")
        for key, value in system.items():
            print(f"  {key}: {value}")
    
    # Check which keys match systems table columns
    if systems:
        system_keys = set(systems[0].keys())
        table_columns = set(columns)
        
        print(f"\nSystem keys: {system_keys}")
        print(f"Table columns: {table_columns}")
        print(f"Missing in table: {system_keys - table_columns}")
        print(f"Extra in table: {table_columns - system_keys}")

if __name__ == "__main__":
    debug_population()
