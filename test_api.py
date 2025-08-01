#!/usr/bin/env python3
import json
from model.traveller_map_api import TravellerMapAPI

# Create API instance
api = TravellerMapAPI()

# Get universe data (contains all sectors)
print("Fetching universe data...")
universe_data = api.get_universe()

# Print the first sector's data structure
if "Sectors" in universe_data and universe_data["Sectors"]:
    print("\nExample sector data structure:")
    print(json.dumps(universe_data["Sectors"][0], indent=2))
    
    # Count sectors
    print(f"\nTotal sectors available: {len(universe_data['Sectors'])}")
    
    # Get detailed data for one sector
    first_sector = universe_data["Sectors"][0]
    sector_name = ""
    if "Names" in first_sector and first_sector["Names"]:
        sector_name = first_sector["Names"][0].get("Text", "")
    if not sector_name and "Abbreviation" in first_sector:
        sector_name = first_sector["Abbreviation"]
    
    if sector_name:
        print(f"\nFetching detailed data for sector: {sector_name}")
        t5_data = api.get_sector_t5(sector_name)
        print(f"T5 data sample (first 500 chars):\n{t5_data[:500]}...")
else:
    print("No sectors found in universe data")
