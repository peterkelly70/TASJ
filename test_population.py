#!/usr/bin/env python3
"""
Test script to verify system and planet population works correctly.
This will test the population function directly and show any errors.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from model.traveller_database import TravellerDatabase
from model.traveller_map_api import TravellerMapAPI
sys.path.append('scripts')
from populate_systems import populate_systems_for_sector

def test_system_population():
    """Test system population for a single sector."""
    print("=== TESTING SYSTEM POPULATION ===")
    
    try:
        # Initialize database and API
        print("Initializing database...")
        db = TravellerDatabase("sqlite")
        print("✅ Database initialized")
        
        api = TravellerMapAPI()
        print("✅ API initialized")
        
        # Test sector data
        sector_data = {
            "name": "Spinward Marches",
            "sector_id": 1,
            "abbreviation": "Spin",
            "milieu": "M1105"
        }
        
        print(f"Testing population for sector: {sector_data['name']}")
        
        # Call population function
        systems_added = populate_systems_for_sector(api, db, sector_data, "M1105")
        
        print(f"✅ SUCCESS: Added {systems_added} systems for sector {sector_data['name']}")
        
        # Verify systems were added
        systems = db.read_records("systems", {"sector_id": 1})
        print(f"✅ Database now contains {len(systems)} systems for this sector")
        
        # Verify planets were added
        planets = db.read_records("planets", {"sector_id": 1})
        print(f"✅ Database now contains {len(planets)} planets for this sector")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_system_population()
    if success:
        print("\n🎉 System population test PASSED")
    else:
        print("\n💥 System population test FAILED")
