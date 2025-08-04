#!/usr/bin/env python3
"""
Script to populate the systems table with data from the Traveller Map API.
This script will:
1. Fetch sector data from the Traveller Map API
2. Extract system data from the sector data
3. Insert the system data into the systems table
4. Create relationships in the sector_has_system table
5. Generate synthetic data for missing systems when API returns 404
"""

import os
import sys
import logging
import json
import random
import string
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Import project modules
from model.traveller_map_api import TravellerMapAPI
from model.traveller_database import TravellerDatabase
from model.sectors_db import SectorDB
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_system_data(sector_name, system_line):
    """
    Parse a line of system data from the T5 format.
    Expected format: Hex Name UWP Bases Zone PBG Allegiance Stellar
    Returns a dictionary with system data.
    """
    parts = system_line.strip().split()
    if len(parts) < 3:
        return None
    
    # Basic system data
    system_data = {
        "hex": parts[0],
        "name": parts[1],
        "uwp": parts[2],
    }
    
    # Optional fields
    if len(parts) > 3:
        system_data["bases"] = parts[3]
    if len(parts) > 4:
        system_data["zone"] = parts[4]
    if len(parts) > 5:
        system_data["pbg"] = parts[5]
    if len(parts) > 6:
        system_data["allegiance_code"] = parts[6]
    if len(parts) > 7:
        system_data["stellar_data"] = " ".join(parts[7:])
    
    # Parse hex coordinates
    try:
        if len(system_data["hex"]) == 4:
            system_data["x"] = int(system_data["hex"][:2])
            system_data["y"] = int(system_data["hex"][2:])
    except ValueError:
        logger.warning(f"Invalid hex format for system {system_data['name']} in sector {sector_name}: {system_data['hex']}")
    
    return system_data

def generate_synthetic_planet_data(system_name, system_hex, planet_number):
    """
    Generate synthetic planet data for a system.
    
    Args:
        system_name: Name of the system
        system_hex: Hex code of the system
        planet_number: Planet number in the system
        
    Returns:
        Dictionary with synthetic planet data
    """
    # Generate a random name
    name_length = random.randint(4, 10)
    name = ''.join(random.choice(string.ascii_letters) for _ in range(name_length)).capitalize()
    
    # Generate a random UWP (Universal World Profile) for the planet
    starport = random.choice('ABCDEFGHX')
    size = random.choice('0123456789A')
    atmosphere = random.choice('0123456789ABCDEF')
    hydrographics = random.choice('0123456789A')
    population = random.choice('0123456789ABCDEF')
    government = random.choice('0123456789ABCDEF')
    law_level = random.choice('0123456789ABCDEF')
    tech_level = random.choice('0123456789ABCDEF')
    uwp = f"{starport}{size}{atmosphere}{hydrographics}{population}{government}{law_level}-{tech_level}"
    
    # Generate other planet attributes
    bases = random.choice(['N', 'S', 'A', 'G', 'R', ''])
    zone = random.choice(['R', 'A', ''])
    pbg = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
    allegiance_code = random.choice(['Im', 'As', 'Na', 'Cs', 'Zh', 'Va', ''])
    
    # Generate planet type based on atmosphere and hydrographics
    planet_types = ['Rocky', 'Desert', 'Ocean', 'Ice', 'Volcanic', 'Jungle', 'Temperate', 'Gas Giant', 'Barren']
    planet_type = random.choice(planet_types)
    
    # Generate a random radius (in km)
    radius = random.randint(1000, 15000)
    
    # Generate random gravity (0.1 to 2.5g)
    gravity = round(random.uniform(0.1, 2.5), 2)
    
    # Generate random temperature (-200 to +500 C)
    temperature = random.randint(-200, 500)
    
    # Generate random day length (in hours)
    day_length = random.randint(10, 100)
    
    # Generate random year length (in local days)
    year_length = random.randint(50, 1000)
    
    planet_data = {
        "name": f"{name} (Synthetic Planet)",
        "system_name": system_name,
        "system_hex": system_hex,
        "planet_number": planet_number,
        "uwp": uwp,
        "bases": bases,
        "zone": zone,
        "pbg": pbg,
        "allegiance_code": allegiance_code,
        "planet_type": planet_type,
        "radius": radius,
        "gravity": gravity,
        "temperature": temperature,
        "day_length": day_length,
        "year_length": year_length,
        "description": f"Synthetic planet {planet_number} in system {system_name}"
    }
    
    return planet_data

def generate_synthetic_system_data(sector_name, num_systems=None):
    """
    Generate synthetic system data when API data is not available.
    
    Args:
        sector_name: Name of the sector
        num_systems: Number of systems to generate, if None will randomize between 10-50
        
    Returns:
        List of dictionaries with synthetic system data
    """
    # If num_systems is not specified, randomize between 10 and 50
    if num_systems is None:
        num_systems = random.randint(10, 50)
        
    logger.info(f"Generating {num_systems} synthetic systems for sector: {sector_name}")
    systems = []
    
    # Traveller sectors are typically 32x40 hexes
    max_x = 32
    max_y = 40
    
    # Generate random positions for systems
    used_positions = set()
    
    for _ in range(num_systems):
        # Generate random position until we find an unused one
        while True:
            x = random.randint(1, max_x)
            y = random.randint(1, max_y)
            pos = (x, y)
            if pos not in used_positions:
                used_positions.add(pos)
                break
                
        # Format hex coordinates as two-digit strings
        hex_x = f"{x:02d}"
        hex_y = f"{y:02d}"
        hex_code = f"{hex_x}{hex_y}"
        
        # Generate a random name
        name_length = random.randint(4, 10)
        name = ''.join(random.choice(string.ascii_letters) for _ in range(name_length)).capitalize()
        
        # Generate a random UWP (Universal World Profile) for the main world
        starport = random.choice('ABCDEFGHX')
        size = random.choice('0123456789A')
        atmosphere = random.choice('0123456789ABCDEF')
        hydrographics = random.choice('0123456789A')
        population = random.choice('0123456789ABCDEF')
        government = random.choice('0123456789ABCDEF')
        law_level = random.choice('0123456789ABCDEF')
        tech_level = random.choice('0123456789ABCDEF')
        uwp = f"{starport}{size}{atmosphere}{hydrographics}{population}{government}{law_level}-{tech_level}"
        
        # Generate other system attributes
        bases = random.choice(['N', 'S', 'A', 'G', 'R', ''])
        zone = random.choice(['R', 'A', ''])
        pbg = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
        allegiance_code = random.choice(['Im', 'As', 'Na', 'Cs', 'Zh', 'Va', ''])
        stellar_data = f"{random.choice(['A', 'B', 'F', 'G', 'K', 'M'])}{random.randint(0, 9)} V"
        
        # Generate random number of planets (1-10)
        num_planets = random.randint(1, 10)
        
        # Store planets in the system data
        planets = []
        for i in range(1, num_planets + 1):
            planet_data = generate_synthetic_planet_data(f"{name} (Synthetic)", hex_code, i)
            planets.append(planet_data)
        
        system_data = {
            "hex": hex_code,
            "name": f"{name} (Synthetic)",
            "uwp": uwp,  # This is the main world's UWP
            "bases": bases,
            "zone": zone,
            "pbg": pbg,
            "allegiance_code": allegiance_code,
            "stellar_data": stellar_data,
            "x": x,
            "y": y,
            "num_planets": num_planets,
            "planets": planets,  # Store planet data for later insertion
            "description": f"Synthetic system generated for {sector_name}"
        }
        
        systems.append(system_data)
    
    return systems

def get_column_names(db, table_name):
    """
    Get column names for a database table.
    
    Args:
        db: TravellerDatabase instance
        table_name: Name of the table
        
    Returns:
        List of column names
    """
    cursor = db.conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def update_existing_system(db, system_data_copy, columns, existing_systems, planets, is_synthetic):
    """
    Update an existing system in the database.
    
    Args:
        db: TravellerDatabase instance
        system_data_copy: Dictionary with system data
        columns: List of column names
        existing_systems: List of existing systems
        planets: List of planet data dictionaries
        is_synthetic: Whether this is a synthetic system
        
    Returns:
        Tuple of (system_id, was_added)
    """
    # Convert tuple to dict using column names
    existing_system = dict(zip(columns, existing_systems[0]))
    # Update existing system
    system_id = existing_system.get("system_id") or existing_system.get("id")
    db.update_record("systems", system_data_copy, {"system_id": system_id})
    system_type = "synthetic" if is_synthetic else ""
    print(f"Successfully updated {system_type} system '{system_data_copy['name']}' (ID: {system_id})")
    logger.info(f"Updated {system_type} system {system_data_copy['name']} (ID: {system_id})")
    
    # Insert or update planets for this system
    if planets:
        num_planets = len(planets)
        print(f"Updating {num_planets} planets for system '{system_data_copy['name']}'")
        insert_planets_for_system(db, planets, system_id)
        print(f"Successfully updated {num_planets} planets for system '{system_data_copy['name']}'")
        
    return system_id, False

def insert_new_system(db, system_data_copy, columns, sector_id, sector_name, planets, is_synthetic):
    """
    Insert a new system into the database.
    
    Args:
        db: TravellerDatabase instance
        system_data_copy: Dictionary with system data
        columns: List of column names
        sector_id: ID of the sector
        sector_name: Name of the sector
        planets: List of planet data dictionaries
        is_synthetic: Whether this is a synthetic system
        
    Returns:
        Tuple of (system_id, was_added)
    """
    # Insert new system
    db.create_record("systems", system_data_copy)
    # Get the ID of the newly inserted system
    new_systems = db.read_records("systems", {"name": system_data_copy["name"], "hex": system_data_copy["hex"]})
    if not new_systems:
        system_type = "synthetic" if is_synthetic else ""
        logger.warning(f"Failed to retrieve ID for newly inserted {system_type} system {system_data_copy['name']}")
        return None, False
        
    # Convert tuple to dict using column names
    new_system = dict(zip(columns, new_systems[0]))
    system_id = new_system.get("system_id") or new_system.get("id")
    
    # Create relationship in sector_has_system table
    relationship_data = {
        "sector_id": sector_id,
        "system_id": system_id
    }
    db.create_record("sector_has_system", relationship_data)
    system_type = "synthetic" if is_synthetic else ""
    logger.debug(f"Added {system_type} system {system_data_copy['name']} (ID: {system_id}) to sector {sector_name}")
    print(f"CONSOLE: Added {system_type} system {system_data_copy['name']} (ID: {system_id}) to sector {sector_name}")
    
    # Insert planets for this system
    if planets:
        print(f"PLANETS: Inserting planets for system {system_data_copy['name']} ({system_data_copy['hex']})")
        print(f"CONSOLE: Processing planets for system {system_data_copy['name']} at {system_data_copy['hex']}")
        insert_planets_for_system(db, planets, system_id)
        
    return system_id, True

def insert_or_update_system(db, system_data, sector_id, sector_name, is_synthetic=False):
    """
    Insert a new system or update an existing one in the database.
    
    Args:
        db: TravellerDatabase instance
        system_data: Dictionary with system data
        sector_id: ID of the sector
        sector_name: Name of the sector
        is_synthetic: Whether this is a synthetic system
        
    Returns:
        Tuple of (system_id, was_added) where system_id is the ID of the system and was_added is True if system was added, False if updated
    """
    try:
        # Make a copy of system_data to avoid modifying the original
        system_data_copy = system_data.copy()
        
        # Remove planets from system_data if present (we'll handle them separately)
        planets = system_data_copy.pop("planets", [])
        system_data_copy.pop("num_planets", None)  # Remove num_planets as it's not a DB column
        
        # Check if system already exists
        existing_systems = db.read_records("systems", {"name": system_data_copy["name"], "hex": system_data_copy["hex"]})
        
        # Get column names to map tuple values to dictionary keys
        columns = get_column_names(db, "systems")
        
        if existing_systems:
            return update_existing_system(db, system_data_copy, columns, existing_systems, planets, is_synthetic)
        else:
            return insert_new_system(db, system_data_copy, columns, sector_id, sector_name, planets, is_synthetic)
    except Exception as e:
        system_type = "synthetic" if is_synthetic else ""
        logger.error(f"Error inserting {system_type} system {system_data_copy['name']}: {e}")
        return None, False

def ensure_planet_tables_exist(db):
    """
    Ensure that the planets and system_has_planet tables exist in the database.
    
    Args:
        db: TravellerDatabase instance
    """
    cursor = db.conn.cursor()
    
    # Check if planets table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planets'")
    planets_table_exists = cursor.fetchone() is not None
    
    if not planets_table_exists:
        # Create planets table if it doesn't exist
        logger.info("Creating planets table")
        cursor.execute("""
            CREATE TABLE planets (
                planet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                system_name TEXT,
                system_hex TEXT,
                planet_number INTEGER,
                uwp TEXT,
                bases TEXT,
                zone TEXT,
                pbg TEXT,
                allegiance_code TEXT,
                planet_type TEXT,
                radius INTEGER,
                gravity REAL,
                temperature INTEGER,
                day_length INTEGER,
                year_length INTEGER,
                description TEXT
            )
        """)
        db.conn.commit()
    
    # Check if system_has_planet table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_has_planet'")
    if not cursor.fetchone():
        logger.info("Creating system_has_planet table")
        cursor.execute("""
            CREATE TABLE system_has_planet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER,
                planet_id INTEGER,
                FOREIGN KEY (system_id) REFERENCES systems(system_id),
                FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
            )
        """)
        db.conn.commit()
    
    # Only check for missing columns if the planets table already existed
    if planets_table_exists:
        # Get current columns in the planets table
        cursor.execute("PRAGMA table_info(planets)")
        existing_columns = {row[1].lower(): row[1] for row in cursor.fetchall()}
        
        # Define required columns with their types
        required_columns = {
            "system_name": "TEXT",
            "system_hex": "TEXT",
            "planet_number": "INTEGER",
            "uwp": "TEXT",
            "bases": "TEXT",
            "zone": "TEXT",
            "pbg": "TEXT",
            "allegiance_code": "TEXT",
            "planet_type": "TEXT",
            "radius": "INTEGER",
            "gravity": "REAL",
            "temperature": "INTEGER",
            "day_length": "INTEGER",
            "year_length": "INTEGER",
            "description": "TEXT"
        }
        
        # Add missing columns
        for col_name, col_type in required_columns.items():
            if col_name.lower() not in existing_columns:
                logger.info(f"Adding missing column '{col_name}' to planets table")
                try:
                    cursor.execute(f"ALTER TABLE planets ADD COLUMN {col_name} {col_type}")
                    db.conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to add column '{col_name}': {e}")
                    # Continue with other columns even if one fails

def update_existing_planet(db, planet_data, existing_planets, columns):
    """
    Update an existing planet in the database.
    
    Args:
        db: TravellerDatabase instance
        planet_data: Dictionary with planet data
        existing_planets: List of existing planets
        columns: List of column names
        
    Returns:
        Planet ID
    """
    # Convert tuple to dict using column names
    existing_planet = dict(zip(columns, existing_planets[0]))
    # Update existing planet
    planet_id = existing_planet.get("planet_id") or existing_planet.get("id")
    db.update_record("planets", planet_data, {"planet_id": planet_id})
    logger.debug(f"Updated planet {planet_data['name']} (ID: {planet_id})")
    print(f"CONSOLE: Updated planet {planet_data['name']} (ID: {planet_id})")
    return planet_id

def insert_new_planet(db, planet_data, system_id, columns):
    """
    Insert a new planet into the database.
    
    Args:
        db: TravellerDatabase instance
        planet_data: Dictionary with planet data
        system_id: ID of the system
        columns: List of column names
        
    Returns:
        Tuple of (planet_id, success)
    """
    # Insert new planet
    db.create_record("planets", planet_data)
    # Get the ID of the newly inserted planet
    new_planets = db.read_records("planets", {"name": planet_data["name"], "system_hex": planet_data["system_hex"]})
    if not new_planets:
        logger.warning(f"Failed to retrieve ID for newly inserted planet {planet_data['name']}")
        return None, False
        
    # Convert tuple to dict using column names
    new_planet = dict(zip(columns, new_planets[0]))
    planet_id = new_planet.get("planet_id") or new_planet.get("id")
    
    # Create relationship in system_has_planet table
    relationship_data = {
        "system_id": system_id,
        "planet_id": planet_id
    }
    db.create_record("system_has_planet", relationship_data)
    logger.debug(f"Added planet {planet_data['name']} (ID: {planet_id}) to system ID: {system_id}")
    print(f"CONSOLE: Added planet {planet_data['name']} (ID: {planet_id}) to system ID: {system_id}")
    return planet_id, True

def insert_planets_for_system(db, planets, system_id):
    """
    Insert planets for a system into the database.
    
    Args:
        db: TravellerDatabase instance
        planets: List of planet data dictionaries
        system_id: ID of the system
        
    Returns:
        Number of planets added
    """
    ensure_planet_tables_exist(db)
    
    # Get column names for the planets table
    columns = get_column_names(db, "planets")
    
    # Get existing planets for this system
    existing_planets = db.read_records("system_has_planet", {"system_id": system_id})
    existing_planet_ids = [p[0] for p in existing_planets]  # Assuming first column is planet_id
    
    planets_added = 0
    planets_updated = 0
    
    for planet_data in planets:
        try:
            # Make a copy to avoid modifying the original
            planet_data = planet_data.copy()
            planet_name = planet_data.get("name", planet_data.get("planet_name", "Unknown"))
            
            # Check if planet already exists for this system
            planet_exists = any(p for p in existing_planets 
                              if p[1] == planet_name or  # Assuming second column is name
                                 p[1] == planet_data.get("planet_name"))
            
            if planet_exists:
                # Update existing planet
                planet_id = update_existing_planet(db, planet_data, existing_planets, columns)
                print(f"Updated planet '{planet_name}' (ID: {planet_id}) in system ID {system_id}")
                logger.info(f"Updated planet {planet_name} (ID: {planet_id}) in system ID {system_id}")
                planets_updated += 1
            else:
                # Insert new planet
                planet_id, success = insert_new_planet(db, planet_data, system_id, columns)
                if success:
                    print(f"Added new planet '{planet_name}' (ID: {planet_id}) to system ID {system_id}")
                    logger.info(f"Added new planet {planet_name} (ID: {planet_id}) to system ID {system_id}")
                    planets_added += 1
                
        except Exception as e:
            error_msg = f"Error processing planet {planet_name}: {e}"
            print(f"ERROR: {error_msg}")
            logger.error(error_msg, exc_info=True)
    
    # Log summary of planet operations
    if planets_added or planets_updated:
        print(f"Planet update summary - Added: {planets_added}, Updated: {planets_updated}")
    
    return planets_added

def insert_systems_batch(db, systems, sector_id, sector_name, is_synthetic=False):
    """
    Insert a batch of systems into the database.
    
    Args:
        db: TravellerDatabase instance
        systems: List of system data dictionaries
        sector_id: ID of the sector
        sector_name: Name of the sector
        is_synthetic: Whether these are synthetic systems
        
    Returns:
        Number of systems added
    """
    systems_added = 0
    
    for system_data in systems:
        system_id, was_added = insert_or_update_system(db, system_data, sector_id, sector_name, is_synthetic)
        if was_added and system_id is not None:
            systems_added += 1
    
    system_type = "synthetic" if is_synthetic else ""
    logger.info(f"Added {systems_added} new {system_type} systems to sector {sector_name}")
    print(f"SYSTEMS POPULATED: Added {systems_added} systems to sector {sector_name}")
    print(f"CONSOLE: Successfully processed {systems_added} systems for sector {sector_name}")
    return systems_added

def populate_systems_for_sector(api, db, sector_data, milieu=None):
    """
    Populate systems for a given sector.
    
    Args:
        api: TravellerMapAPI instance
        db: TravellerDatabase instance
        sector_data: Dictionary with sector data
        milieu: Optional milieu code
    
    Returns:
        Number of systems added
    """
    sector_name = sector_data.get("name")
    sector_id = sector_data.get("sector_id") or sector_data.get("id")
    
    if not sector_name or not sector_id:
        logger.error(f"Invalid sector data: {sector_data}")
        return 0
    
    logger.info(f"Fetching systems for sector: {sector_name} (ID: {sector_id})")
    print(f"FETCHING SYSTEMS: Starting system population for sector: {sector_name} (ID: {sector_id})")
    try:
        print(f"CONSOLE: Starting population for sector {sector_name}")
        
        # Use T5 format to get actual system data
        print(f"CONSOLE: Fetching T5 data for sector {sector_name}")
        t5_data = api.get_sector_t5(sector_name, milieu)
        
        # Parse T5 data to extract systems
        systems = api._parse_t5_systems(t5_data)
        
        print(f"CONSOLE: Parsed {len(systems)} systems from T5 data")
        
        if not systems:
            logger.warning(f"No systems found for sector {sector_name}")
            print(f"CONSOLE: No systems found for sector {sector_name}")
            return 0
        
        logger.info(f"Found {len(systems)} systems in sector {sector_name}")
        print(f"CONSOLE: Found {len(systems)} systems in sector {sector_name}")
        print(f"CONSOLE: Processing {len(systems)} systems for sector {sector_name}")
        
        # T5 data is already in correct format, just add sector info
        # Filter system data to only include valid system-level columns
        valid_system_columns = {
            'name', 'hex', 'uwp', 'bases', 'zone', 'pbg', 'allegiance_code', 
            'stellar_data', 'x', 'y', 'description', 'image_path', 'trade_codes'
        }
        
        formatted_systems = []
        for system in systems:
            # Only keep valid system-level columns
            filtered_system = {k: v for k, v in system.items() if k in valid_system_columns}
            filtered_system['sector_id'] = sector_id
            filtered_system['milieu'] = milieu
            formatted_systems.append(filtered_system)
        
        print(f"CONSOLE: Successfully formatted {len(formatted_systems)} systems for processing")
        
        # Insert systems into database
        systems_added = insert_systems_batch(db, formatted_systems, sector_id, sector_name)
        print(f"CONSOLE: Successfully processed {systems_added} systems for sector {sector_name}")
        return systems_added
    
    except Exception as e:
        logger.error(f"Error populating systems for sector {sector_name}: {e}")
        print(f"ERROR: Failed to populate systems for sector {sector_name}: {e}")
        logger.info(f"Falling back to synthetic system generation for sector {sector_name}")
        
        # Generate synthetic system data as fallback
        systems = generate_synthetic_system_data(sector_name)
        if not systems:
            logger.error(f"Failed to generate synthetic systems for sector {sector_name}")
            return 0
            
        # Continue with inserting the synthetic systems
        logger.info(f"Found {len(systems)} synthetic systems for sector {sector_name}")
        
        # Insert synthetic systems into database
        return insert_systems_batch(db, systems, sector_id, sector_name, is_synthetic=True)

def main():
    """Main function to populate systems table."""
    # Load environment variables
    load_dotenv("config/.env")
    
    # Database path is loaded from .env by TravellerDatabase
    
    # Initialize API and database
    api = TravellerMapAPI()
    # TravellerDatabase is a singleton that reads db_path from .env
    db = TravellerDatabase("sqlite")
    sector_db = SectorDB(db)
    
    # Get current milieu from settings
    milieu = os.getenv('DEFAULT_MILIEU', 'M1105')
    
    # Get all sectors
    sectors = sector_db.get_all_sectors()
    logger.info(f"Found {len(sectors)} sectors in database")
    
    # Populate systems for each sector
    total_systems_added = 0
    for sector in sectors:
        systems_added = populate_systems_for_sector(api, db, sector, milieu)
        total_systems_added += systems_added
    
    logger.info(f"Total systems added: {total_systems_added}")

if __name__ == "__main__":
    main()
