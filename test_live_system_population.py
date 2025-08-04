#!/usr/bin/env python3
"""
Test live system population logging in the app
"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Add project root to path
sys.path.append(os.getcwd())

from scripts.populate_systems import populate_systems_for_sector
from model.traveller_map_api import TravellerMapAPI
from model.database import Database
from dotenv import load_dotenv

load_dotenv()

def test_live_population():
    """Test system population with live console logging"""
    print("=== TESTING LIVE SYSTEM POPULATION LOGGING ===")
    
    # Initialize database and API
    db = Database()
    api = TravellerMapAPI()
    milieu = os.getenv('DEFAULT_MILIEU', 'M1105')
    
    # Test with Spinward Marches (known to have data)
    sector_name = 'Spinward Marches'
    sector_id = 1  # Use existing sector ID
    
    print(f"Testing system population for: {sector_name}")
    print("=" * 50)
    
    # This will show all console logging
    systems_added = populate_systems_for_sector(db, api, sector_name, sector_id, milieu)
    
    print("=" * 50)
    print(f"✅ System population test completed")
    print(f"✅ Added {systems_added} systems to sector {sector_name}")

if __name__ == "__main__":
    test_live_population()
