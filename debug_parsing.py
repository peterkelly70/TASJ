#!/usr/bin/env python3
"""
Debug T5 parsing to see what's happening
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
print(f"=== DEBUGGING T5 PARSING FOR {sector_name} ===")

try:
    # Get T5 data
    t5_data = api.get_sector_t5(sector_name, milieu)
    
    # Debug the parsing step by step
    lines = t5_data.split('\n')
    print(f"Total lines: {len(lines)}")
    
    system_count = 0
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Skip header lines
        if line.startswith('Hex') or line.startswith('----'):
            continue
            
        # Check if this is a system line
        is_system = api._is_system_line(line)
        print(f"Line {i+1}: '{line}' -> is_system: {is_system}")
        
        if is_system:
            system_count += 1
            parsed = api._parse_system_line(line)
            print(f"  Parsed: {parsed}")
            
        if system_count >= 3:  # Show first few systems
            break
    
    # Test full parsing
    systems = api._parse_t5_systems(t5_data)
    print(f"\nFull parsing result: {len(systems)} systems")
    
    if systems:
        print("First few systems:")
        for i, system in enumerate(systems[:3]):
            print(f"  {i+1}: {system}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
