#!/usr/bin/env python
"""
Script to import missing sectors (like Spinward Marches and Delphi) and their systems
from the Traveller Map API into the local database.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.traveller_database import TravellerDatabase
from model.traveller_map_api import TravellerMapAPI
from model.sectors_db import SectorDB

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_sectors_and_systems(db_path: str, milieu: str = "M1105", 
                              target_sectors: Optional[List[str]] = None):
    """
    Import sectors and their systems from the Traveller Map API into the local database.
    
    Args:
        db_path: Path to the SQLite database
        milieu: Milieu code to use for data import
        target_sectors: Optional list of sector names to specifically import
                       (if None, will import all sectors)
    """
    logger.info(f"Connecting to database at {db_path}")
    
    # Set the DATABASE_FILE_PATH environment variable to our db_path
    os.environ['DATABASE_FILE_PATH'] = db_path
    
    # Initialize the database with SQLite type
    db = TravellerDatabase("sqlite")
    sectors_db = SectorDB(db)
    api = TravellerMapAPI(milieu=milieu)
    
    # Get universe data from API
    logger.info(f"Fetching universe data for milieu {milieu}")
    universe = api.get_universe(milieu)
    
    # Filter sectors if target_sectors is provided
    sectors_to_import = universe['Sectors']
    if target_sectors:
        sectors_to_import = [
            s for s in sectors_to_import 
            if any(target.lower() in name.get('Text', '').lower() 
                  for name in s['Names'] 
                  for target in target_sectors)
        ]
        logger.info(f"Filtered to {len(sectors_to_import)} target sectors")
    
    total_sectors = len(sectors_to_import)
    logger.info(f"Found {total_sectors} sectors to process")
    
    # Process each sector
    for i, sector_data in enumerate(sectors_to_import, 1):
        # Extract sector name from the Names list
        sector_name = sector_data['Names'][0]['Text'] if sector_data['Names'] else f"Unknown-{i}"
        abbreviation = sector_data.get('Abbreviation', '')
        
        logger.info(f"Processing sector {i}/{total_sectors}: {sector_name} ({abbreviation})")
        
        # Prepare sector data for database
        db_sector_data = {
            'name': sector_name,
            'x_coordinate': sector_data.get('X', 0),
            'y_coordinate': sector_data.get('Y', 0),
            'abbreviation': abbreviation,
            'milieu': milieu,
            'description': f"Sector {sector_name} ({abbreviation}) - {sector_data.get('Tags', '')}"
        }
        
        # Upsert sector into database
        result = sectors_db.upsert_sector(db_sector_data)
        if result:
            logger.info(f"Successfully upserted sector {sector_name}")
        else:
            logger.error(f"Failed to upsert sector {sector_name}")
            continue
        
        # Get sector ID for system relationships
        sector_record = sectors_db.get_sector_by_name(sector_name)
        if not sector_record:
            logger.error(f"Could not retrieve sector ID for {sector_name}")
            continue
            
        sector_id = sector_record[0]  # First column is sector_id
        
        # Import systems for this sector
        import_systems_for_sector(db, api, sector_name, sector_id, milieu)

def import_systems_for_sector(db, api, sector_name, sector_id, milieu):
    # Fetch systems for this sector
    logger.info(f"Fetching systems for sector {sector_name}")
    try:
        # Get sector data in SEC format
        sec_data = api.get_sector_sec(sector_name, milieu=milieu)
        
        # Parse the SEC data to extract systems
        systems = []
        for line in sec_data.strip().split('\n'):
            if line and not line.startswith('#'):
                system_data = api.parse_sec_line(line)
                if system_data:
                    systems.append(system_data)
        
        if not systems:
            logger.warning(f"No systems found for sector {sector_name}")
            return
            
        logger.info(f"Found {len(systems)} systems for sector {sector_name}")
        
        # Process each system
        for system in systems:
            # Extract system data from parsed SEC line
            hex_code = system.get('hex', '')
            system_name = system.get('name', f"System-{hex_code}")
            
            # Prepare system data
            system_data = {
                'name': system_name,
                'hex': hex_code,
                'uwp': system.get('upp', ''),  # UWP is called 'upp' in parsed SEC data
                'allegiance_code': system.get('allegiance', ''),  
                'sector_id': sector_id,
                'milieu': milieu
            }
            
            # Extract additional data from raw_data if available
            if 'raw_data' in system:
                raw_parts = system['raw_data'].split()
                if len(raw_parts) >= 1:
                    system_data['bases'] = raw_parts[0]
                if len(raw_parts) >= 2:
                    system_data['zone'] = raw_parts[1]
                if len(raw_parts) >= 3:
                    system_data['allegiance_code'] = raw_parts[2]
                if len(raw_parts) >= 4:
                    system_data['stellar_data'] = raw_parts[3]
            
            # Insert system into database
            try:
                # Check if system already exists
                existing = db.read_records("systems", {"hex": hex_code, "sector_id": sector_id})
                
                if existing:
                    # Update existing system
                    db.update_record("systems", system_data, {"hex": hex_code, "sector_id": sector_id})
                    logger.debug(f"Updated system {system_name} ({hex_code})")
                else:
                    # Insert new system
                    db.create_record("systems", system_data)
                    logger.debug(f"Inserted system {system_name} ({hex_code})")
                
                # Get system ID for planet relationships
                system_record = db.read_records("systems", {"hex": hex_code, "sector_id": sector_id})
                if system_record:
                    system_id = system_record[0][0]  # First column is system_id
                    
                    # Create sector_has_system relationship if it doesn't exist
                    relation_data = {
                        "sector_id": sector_id,
                        "system_id": system_id
                    }
                    
                    existing_relation = db.read_records("sector_has_system", relation_data)
                    if not existing_relation:
                        db.create_record("sector_has_system", relation_data)
                        logger.debug(f"Created sector-system relationship for {system_name}")
                    
                    # Import planets for this system
                    import_planets_for_system(db, system, system_id, sector_name, milieu)
                    
            except Exception as e:
                logger.error(f"Error processing system {system_name}: {e}")
                
    except Exception as e:
        logger.error(f"Error fetching systems for sector {sector_name}: {e}")

def import_planets_for_system(db, system, system_id, sector_name, milieu):
    """Import planets for a specific system."""
    # In this simplified version, we'll just create a main planet for each system
    # based on the UWP data
    
    hex_code = system.get('Hex', '')
    system_name = system.get('Name', f"System-{hex_code}")
    uwp = system.get('UWP', '')
    
    # Only proceed if we have UWP data
    if not uwp or len(uwp) < 7:
        return
        
    # Create a main planet for the system
    planet_data = {
        'name': system_name,  # Use system name for main planet
        'system_id': system_id,
        'uwp': uwp,
        'size': uwp[2] if len(uwp) > 2 else '0',
        'atmosphere': uwp[3] if len(uwp) > 3 else '0',
        'hydrographics': uwp[4] if len(uwp) > 4 else '0',
        'population': uwp[5] if len(uwp) > 5 else '0',
        'government': uwp[6] if len(uwp) > 6 else '0',
        'law_level': uwp[7] if len(uwp) > 7 else '0',
        'tech_level': uwp[8] if len(uwp) > 8 else '0',
        'system_hex': hex_code,
        'system_name': system_name,
        'sector_name': sector_name,
        'milieu': milieu
    }
    
    try:
        # Check if planet already exists
        existing = db.read_records("planets", {"system_id": system_id, "name": system_name})
        
        if existing:
            # Update existing planet
            db.update_record("planets", planet_data, {"system_id": system_id, "name": system_name})
            logger.debug(f"Updated planet {system_name}")
        else:
            # Insert new planet
            db.create_record("planets", planet_data)
            logger.debug(f"Inserted planet {system_name}")
            
        # Get planet ID for system-planet relationship
        planet_record = db.read_records("planets", {"system_id": system_id, "name": system_name})
        if planet_record:
            planet_id = planet_record[0][0]  # First column is planet_id
            
            # Create system_has_planet relationship if it doesn't exist
            relation_data = {
                "system_id": system_id,
                "planet_id": planet_id
            }
            
            existing_relation = db.read_records("system_has_planet", relation_data)
            if not existing_relation:
                db.create_record("system_has_planet", relation_data)
                logger.debug(f"Created system-planet relationship for {system_name}")
                
    except Exception as e:
        logger.error(f"Error processing planet for system {system_name}: {e}")

if __name__ == "__main__":
    # Get database path from environment or use default
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/.env"))
    db_path = os.getenv('DATABASE_FILE_PATH', './database/traveller_campaign.db')
    
    # Ensure db_path is absolute
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path))
        
    logger.info(f"Using database path: {db_path}")
    
    # Target specific sectors of interest
    target_sectors = ["Spinward", "Delphi", "Core", "Solomani", "Deneb"]
    
    logger.info(f"Starting import of missing sectors to {db_path}")
    import_sectors_and_systems(db_path, "M1105", target_sectors)
    logger.info("Import complete")
