#!/usr/bin/env python3
"""
Sector Data Restoration Script

This script updates the sectors table with complete data from the Traveller Map API.
It matches existing sectors by name or abbreviation and updates their coordinates,
descriptions, and other missing information.
"""

import os
import json
import sqlite3
import time
from model.traveller_map_api import TravellerMapAPI

# Get database path from environment or use default
DB_PATH = os.environ.get('DATABASE_FILE_PATH', 'database/traveller_campaign.db')

def get_db_connection():
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_existing_sectors():
    """Get all sectors from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sectors")
    sectors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sectors

def update_sector(sector_id, data):
    """Update a sector with new data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build the update query dynamically based on available data
    update_fields = []
    params = []
    
    if 'x_coordinate' in data:
        update_fields.append("x_coordinate = ?")
        params.append(data['x_coordinate'])
    
    if 'y_coordinate' in data:
        update_fields.append("y_coordinate = ?")
        params.append(data['y_coordinate'])
    
    if 'description' in data:
        update_fields.append("description = ?")
        params.append(data['description'])
    
    if 'image_path' in data:
        update_fields.append("image_path = ?")
        params.append(data['image_path'])
    
    if not update_fields:
        return False  # Nothing to update
    
    # Add sector_id to params
    params.append(sector_id)
    
    # Execute the update
    query = f"UPDATE sectors SET {', '.join(update_fields)} WHERE sector_id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    
    return True

def download_sector_image(api, sector_name):
    """Download sector image and return the local path"""
    try:
        image_path = api.download_sector_image(sector_name)
        return image_path
    except Exception as e:
        print(f"Error downloading image for {sector_name}: {e}")
        return None

def main():
    print("Starting sector data restoration...")
    
    # Create API instance
    api = TravellerMapAPI()
    
    # Get existing sectors from database
    existing_sectors = get_existing_sectors()
    print(f"Found {len(existing_sectors)} sectors in the database")
    
    # Create lookup dictionaries for faster matching
    sectors_by_name = {s['name'].lower(): s for s in existing_sectors if s['name']}
    sectors_by_abbr = {s['abbreviation'].lower(): s for s in existing_sectors if s['abbreviation']}
    
    # Get universe data from API
    print("Fetching universe data from Traveller Map API...")
    universe_data = api.get_universe()
    
    if "Sectors" not in universe_data:
        print("Error: No sectors found in API response")
        return
    
    api_sectors = universe_data["Sectors"]
    print(f"Found {len(api_sectors)} sectors in the API")
    
    # Track statistics
    updated_count = 0
    not_found_count = 0
    not_found_sectors = []
    
    # Process each API sector
    for api_sector in api_sectors:
        # Extract sector name and abbreviation
        sector_name = ""
        if "Names" in api_sector and api_sector["Names"]:
            sector_name = api_sector["Names"][0].get("Text", "")
        
        abbreviation = api_sector.get("Abbreviation", "")
        
        if not sector_name and not abbreviation:
            continue
        
        # Try to match with existing sector
        db_sector = None
        if sector_name and sector_name.lower() in sectors_by_name:
            db_sector = sectors_by_name[sector_name.lower()]
        elif abbreviation and abbreviation.lower() in sectors_by_abbr:
            db_sector = sectors_by_abbr[abbreviation.lower()]
        
        if not db_sector:
            not_found_count += 1
            not_found_sectors.append(f"{sector_name} ({abbreviation})")
            continue
        
        # Prepare update data
        update_data = {}
        
        # Add coordinates if available
        if "X" in api_sector:
            update_data["x_coordinate"] = api_sector["X"]
        if "Y" in api_sector:
            update_data["y_coordinate"] = api_sector["Y"]
        
        # Add description (using Tags for now)
        if "Tags" in api_sector:
            update_data["description"] = api_sector["Tags"]
        
        # Download sector image if needed
        if not db_sector.get('image_path') and sector_name:
            image_path = download_sector_image(api, sector_name)
            if image_path:
                update_data["image_path"] = image_path
        
        # Update the sector in the database
        if update_data:
            success = update_sector(db_sector['sector_id'], update_data)
            if success:
                updated_count += 1
                print(f"Updated sector: {sector_name} ({abbreviation})")
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    # Print summary
    print("\nUpdate Summary:")
    print(f"Total sectors in database: {len(existing_sectors)}")
    print(f"Total sectors in API: {len(api_sectors)}")
    print(f"Sectors updated: {updated_count}")
    print(f"Sectors not found in database: {not_found_count}")
    
    if not_found_sectors:
        print("\nFirst 10 sectors not found in database:")
        for i, sector in enumerate(not_found_sectors[:10]):
            print(f"  {i+1}. {sector}")
        
        if len(not_found_sectors) > 10:
            print(f"  ... and {len(not_found_sectors) - 10} more")

if __name__ == "__main__":
    main()
