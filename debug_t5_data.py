#!/usr/bin/env python3
"""
Debug T5 data to see actual system data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.traveller_map_api import TravellerMapAPI
from dotenv import load_dotenv

load_dotenv()

api = TravellerMapAPI()
milieu = os.getenv('DEFAULT_MILIEU', 'M1105')

# Test with a sector that should have data
sector_name = 'Spinward Marches'
print(f"=== DEBUGGING T5 DATA FOR {sector_name} ===")

try:
    # Get T5 data
    t5_data = api.get_sector_t5(sector_name, milieu)
    
    print("T5 Data preview (first 1000 chars):")
    print(t5_data[:1000])
    print("\n" + "="*50 + "\n")
    
    # Count lines
    lines = t5_data.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Show system lines (lines that aren't comments)
    system_lines = [line for line in lines if line.strip() and not line.startswith('#')]
    print(f"System lines: {len(system_lines)}")
    
    # Show first few system lines
    print("First 5 system lines:")
    for i, line in enumerate(system_lines[:5]):
        print(f"  {i+1}: {line}")
    
    # Parse systems to verify the parsing works
    systems = api._parse_t5_systems(t5_data)
    print(f"\nParsed systems: {len(systems)}")
    
    if systems:
        print("First system:")
        for k, v in systems[0].items():
            print(f"  {k}: {v}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
