#!/usr/bin/env python3
"""
Sector Data Synchronization Script

This script synchronizes the local database with the Traveller Map API data.
It will:
1. Add any missing sectors from the API
2. Update existing sectors with the latest data
3. Handle all sector fields including coordinates, descriptions, and images
4. Support milieu-specific data
"""

import os
import re
import sqlite3
import time
import logging
from typing import Dict, List, Optional, Any
from model.traveller_map_api import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sector_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# Get database path from environment or use default
DB_PATH = os.environ.get('DATABASE_FILE_PATH', 'database/traveller_campaign.db')
# Default milieu to use if not specified
DEFAULT_MILIEU = "M1105"
# Delay between API requests to avoid rate limiting
API_DELAY = 0.5  # seconds

class SectorSynchronizer:
    """Handles synchronization of sector data between the database and Traveller Map API."""
    
    def __init__(self, db_path: str = DB_PATH, milieu: str = DEFAULT_MILIEU):
        """Initialize the synchronizer with database path and milieu."""
        self.db_path = db_path
        self.milieu = milieu
        self.api = TravellerMapAPI(milieu=milieu)
        self.stats = {
            'total_in_db': 0,
            'total_in_api': 0,
            'sectors_created': 0,
            'sectors_updated': 0,
            'sectors_skipped': 0,
            'systems_created': 0,
            'systems_updated': 0,
            'planets_created': 0,
            'planets_updated': 0,
            'errors': 0
        }

    def get_db_connection(self) -> sqlite3.Connection:
        """Create a database connection to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def get_existing_sectors(self) -> List[Dict]:
        """Get all sectors from the database."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sectors")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching sectors: {e}")
            return []

    def create_sector(self, data: Dict[str, Any]) -> bool:
        """Create a new sector in the database."""
        required_fields = ['name', 'abbreviation', 'x_coordinate', 'y_coordinate']
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields to create sector: {data}")
            return False

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sectors 
                    (name, abbreviation, x_coordinate, y_coordinate, 
                     description, image_path, milieu)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['name'],
                    data['abbreviation'],
                    data['x_coordinate'],
                    data['y_coordinate'],
                    data.get('description', ''),
                    data.get('image_path', ''),
                    data.get('milieu', self.milieu)
                ))
                conn.commit()
                logger.info(f"Created new sector: {data['name']} ({data['abbreviation']})")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error creating sector {data.get('name')}: {e}")
            return False

    def update_sector(self, sector_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing sector in the database."""
        if not data:
            return False

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Build the update query dynamically
                update_fields = []
                params = []
                
                for field in ['name', 'abbreviation', 'x_coordinate', 'y_coordinate', 
                            'description', 'image_path', 'milieu']:
                    if field in data and data[field] is not None:
                        update_fields.append(f"{field} = ?")
                        params.append(data[field])
                
                if not update_fields:
                    return False  # Nothing to update
                
                # Add sector_id to params
                params.append(sector_id)
                
                # Execute the update
                query = f"""
                    UPDATE sectors 
                    SET {', '.join(update_fields)}
                    WHERE sector_id = ?
                """
                cursor.execute(query, params)
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating sector {sector_id}: {e}")
            return False

    def download_sector_image(self, sector_name: str) -> Optional[str]:
        """Download sector image and return the local path."""
        try:
            logger.info(f"Downloading image for {sector_name}...")
            # Add a small delay to avoid rate limiting
            time.sleep(API_DELAY)
            return self.api.download_sector_image(sector_name)
        except Exception as e:
            logger.warning(f"Error downloading image for {sector_name}: {e}")
            return None

    def process_sector(self, api_sector: Dict, existing_sectors: Dict) -> None:
        """Process a single sector from the API."""
        try:
            # Extract basic info
            sector_name = ""
            if "Names" in api_sector and api_sector["Names"] and isinstance(api_sector["Names"], list):
                # Handle case where Names is a list of dicts
                if api_sector["Names"] and isinstance(api_sector["Names"][0], dict):
                    sector_name = api_sector["Names"][0].get("Text", "")
                # Handle case where Names is a list of strings
                elif api_sector["Names"] and isinstance(api_sector["Names"][0], str):
                    sector_name = api_sector["Names"[0]]
            
            # Handle case where Abbreviation might be missing or in a different format
            abbreviation = ""
            if "Abbreviation" in api_sector:
                if isinstance(api_sector["Abbreviation"], str):
                    abbreviation = api_sector["Abbreviation"]
                elif isinstance(api_sector["Abbreviation"], dict) and "Text" in api_sector["Abbreviation"]:
                    abbreviation = api_sector["Abbreviation"]["Text"]
            
            if not sector_name and not abbreviation:
                logger.warning("Sector missing both name and abbreviation, skipping")
                self.stats['sectors_skipped'] += 1
                return

            # Prepare sector data
            sector_data = {
                'name': sector_name,
                'abbreviation': abbreviation,
                'x_coordinate': api_sector.get("X"),
                'y_coordinate': api_sector.get("Y"),
                'description': ", ".join(api_sector.get("Tags", [])),
                'milieu': self.milieu
            }

            # Try to find existing sector
            db_sector = None
            if sector_name and sector_name.lower() in existing_sectors['by_name']:
                db_sector = existing_sectors['by_name'][sector_name.lower()]
            elif abbreviation and abbreviation.lower() in existing_sectors['by_abbr']:
                db_sector = existing_sectors['by_abbr'][abbreviation.lower()]

            # Process the sector
            if db_sector:
                # Update existing sector
                if self.update_sector(db_sector['sector_id'], sector_data):
                    self.stats['sectors_updated'] += 1
                    logger.info(f"Updated sector: {sector_name} ({abbreviation})")
                else:
                    self.stats['errors'] += 1
            else:
                # Create new sector
                if self.create_sector(sector_data):
                    self.stats['sectors_created'] += 1
                    logger.info(f"Created new sector: {sector_name} ({abbreviation})")
                else:
                    self.stats['errors'] += 1

            # Get the sector ID (either existing or newly created)
            sector_id = None
            if db_sector:
                sector_id = db_sector['sector_id']
            else:
                # For new sectors, get the ID from the database
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT sector_id FROM sectors WHERE name = ?", 
                        (sector_name,)
                    )
                    result = cursor.fetchone()
                    if result:
                        sector_id = result['sector_id']
            
            # Process systems and planets for this sector
            if sector_id:
                logger.info(f"Processing systems and planets for {sector_name}...")
                try:
                    self.process_systems_and_planets(sector_id, sector_name)
                except Exception as e:
                    logger.error(f"Error processing systems/planets for {sector_name}: {e}")
                    self.stats['errors'] += 1
            
            # Download image if needed
            if not db_sector or not db_sector.get('image_path'):
                image_path = self.download_sector_image(sector_name)
                if image_path:
                    update_data = {'image_path': image_path}
                    if db_sector:
                        self.update_sector(db_sector['sector_id'], update_data)
                    # For new sectors, we'll update the image path in the next sync

        except Exception as e:
            logger.error(f"Error processing sector {sector_name}: {e}")
            self.stats['errors'] += 1

    def get_or_create_system(self, sector_id: int, system_data: Dict) -> Optional[int]:
        """Get an existing system or create a new one."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Try to find existing system
                cursor.execute(
                    "SELECT system_id FROM systems WHERE sector_id = ? AND hex = ?",
                    (sector_id, system_data.get('hex'))
                )
                result = cursor.fetchone()
                
                if result:
                    return result['system_id']
                
                # Create new system
                cursor.execute("""
                    INSERT INTO systems (
                        sector_id, name, hex, uwp, bases, zone, pbg, 
                        allegiance_code, stellar_data, x, y, description, milieu
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sector_id,
                    system_data.get('name', ''),
                    system_data.get('hex'),
                    system_data.get('uwp'),
                    system_data.get('bases'),
                    system_data.get('zone'),
                    system_data.get('pbg'),
                    system_data.get('allegiance_code'),
                    system_data.get('stellar_data'),
                    system_data.get('x'),
                    system_data.get('y'),
                    system_data.get('description'),
                    self.milieu
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_system: {e}")
            return None

    def update_or_create_planet(self, sector_id: int, planet_data: Dict) -> bool:
        """Update or create a planet in the database."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if planet exists
                cursor.execute(
                    "SELECT planet_id FROM planets WHERE system_name = ? AND hex = ?",
                    (planet_data.get('system_name'), planet_data.get('hex'))
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing planet
                    update_fields = []
                    params = []
                    
                    for field in ['name', 'x_coordinate', 'y_coordinate', 'UPP', 'starport', 'size',
                                'atmosphere', 'hydrographics', 'population', 'government', 'law_level',
                                'tech_level', 'allegiance', 'stellar', 'gas_giant', 'bases', 'trade_codes',
                                'travel_code', 'importance', 'economic', 'hex', 'subsector_id', 'travel_zone',
                                'pbg', 'UWP', 'system_hex', 'planet_number', 'zone', 'allegiance_code',
                                'planet_type', 'radius', 'gravity', 'temperature', 'day_length', 'year_length']:
                        if field in planet_data and planet_data[field] is not None:
                            update_fields.append(f"{field} = ?")
                            params.append(planet_data[field])
                    
                    if update_fields:
                        params.append(result['planet_id'])
                        query = f"UPDATE planets SET {', '.join(update_fields)} WHERE planet_id = ?"
                        cursor.execute(query, params)
                        self.stats['planets_updated'] += 1
                else:
                    # Create new planet
                    cursor.execute("""
                        INSERT INTO planets (
                            name, sector_id, x_coordinate, y_coordinate, UPP, description,
                            starport, size, atmosphere, hydrographics, population, government,
                            law_level, tech_level, allegiance, stellar, gas_giant, bases,
                            trade_codes, travel_code, importance, economic, hex, subsector_id,
                            travel_zone, pbg, UWP, system_name, system_hex, planet_number,
                            zone, allegiance_code, planet_type, radius, gravity, temperature,
                            day_length, year_length
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        planet_data.get('name'),
                        planet_data.get('sector_id'),
                        planet_data.get('x_coordinate'),
                        planet_data.get('y_coordinate'),
                        planet_data.get('UPP'),
                        planet_data.get('description'),
                        planet_data.get('starport'),
                        planet_data.get('size'),
                        planet_data.get('atmosphere'),
                        planet_data.get('hydrographics'),
                        planet_data.get('population'),
                        planet_data.get('government'),
                        planet_data.get('law_level'),
                        planet_data.get('tech_level'),
                        planet_data.get('allegiance'),
                        planet_data.get('stellar'),
                        planet_data.get('gas_giant'),
                        planet_data.get('bases'),
                        planet_data.get('trade_codes'),
                        planet_data.get('travel_code'),
                        planet_data.get('importance'),
                        planet_data.get('economic'),
                        planet_data.get('hex'),
                        planet_data.get('subsector_id'),
                        planet_data.get('travel_zone'),
                        planet_data.get('pbg'),
                        planet_data.get('UWP'),
                        planet_data.get('system_name'),
                        planet_data.get('system_hex'),
                        planet_data.get('planet_number'),
                        planet_data.get('zone'),
                        planet_data.get('allegiance_code'),
                        planet_data.get('planet_type'),
                        planet_data.get('radius'),
                        planet_data.get('gravity'),
                        planet_data.get('temperature'),
                        planet_data.get('day_length'),
                        planet_data.get('year_length')
                    ))
                    self.stats['planets_created'] += 1
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error in update_or_create_planet: {e}")
            return False

    def process_systems_and_planets(self, sector_id: int, sector_name: str) -> None:
        """Fetch and process systems and planets for a sector."""
        try:
            logger.info(f"\nProcessing sector: {sector_name}")
            logger.info("=" * 50)
            
            # Get sector data in T5 format
            logger.debug(f"Fetching T5 data for sector: {sector_name}")
            try:
                t5_data = self.api.get_sector_t5(sector_name)
                if not t5_data or not t5_data.strip():
                    logger.warning(f"No T5 data returned for sector {sector_name}")
                    return
            except Exception as e:
                logger.error(f"Failed to fetch T5 data for sector {sector_name}: {e}")
                return
            
            # Log raw T5 data to a file for inspection
            with open(f"t5_debug_{sector_name}.txt", "w", encoding="utf-8") as f:
                f.write(t5_data)
                
            logger.debug(f"Raw T5 data (first 500 chars):\n{t5_data[:500]}...")
            
            # Log the first few lines for debugging
            lines = t5_data.split('\n')
            logger.debug(f"First 10 lines of T5 data:")
            for i, line in enumerate(lines[:10]):
                logger.debug(f"{i+1}: {line}")
            
            # Parse the T5 data
            systems = []
            current_system = None
            
            for line in t5_data.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check if this is a system line (starts with hex code XXXX where X is 0-9 or A-F)
                if (len(line) >= 4 and 
                    all(c in '0123456789ABCDEF' for c in line[:4]) and 
                    (len(line) == 4 or line[4] == ' ')):
                    
                    hex_code = line[:4].strip()
                    rest_of_line = line[4:].strip()
                    
                    # If we have a current system, add it to the list before starting a new one
                    if current_system:
                        systems.append(current_system)
                    
                    # Split the rest of the line into parts
                    parts = rest_of_line.split()
                    
                    if not parts:
                        # No name or data, just a hex code
                        system_name = f"Unnamed System ({hex_code})"
                        uwp = None
                    else:
                        # First part is the system name
                        system_name = parts[0]
                        
                        # Look for UWP in the remaining parts (starts with a letter, contains a dash)
                        uwp = None
                        for part in parts[1:]:
                            if '-' in part and part[0].isalpha() and len(part) >= 7:
                                uwp = part
                                break
                    
                    # Create a new system
                    current_system = {
                        'name': system_name,
                        'hex': hex_code,
                        'planets': []
                    }
                    
                    if uwp:
                        current_system['UWP'] = uwp
                    
                    # Add the first planet (the main world) with the same UWP as the system
                    if uwp and uwp != '???????':
                        # Parse the UWP to extract trade codes and other info
                        planet_data = {
                            'name': f"{system_name} I",
                            'UWP': uwp,
                            'is_main_world': True
                        }
                        
                        # Extract trade codes and bases from the rest of the line if present
                        trade_codes = []
                        bases = []
                        
                        # Look for trade codes in parentheses
                        trade_match = re.search(r'\(([A-Za-z0-9\s,]+)\)', rest_of_line)
                        if trade_match:
                            trade_codes = [tc.strip() for tc in trade_match.group(1).split(',') if tc.strip()]
                            planet_data['trade_codes'] = ', '.join(trade_codes)
                        
                        # Look for bases (N, S, X, W)
                        if 'N' in rest_of_line:
                            bases.append('N')
                        if 'S' in rest_of_line:
                            bases.append('S')
                        if 'X' in rest_of_line:
                            bases.append('X')
                        if 'W' in rest_of_line:
                            bases.append('W')
                        
                        if bases:
                            planet_data['bases'] = ''.join(bases)
                        
                        current_system['planets'].append(planet_data)
                    
                    logger.debug(f"Found system: {system_name} at {hex_code} with UWP: {uwp}")
                
                # Check for additional planets in the system (indented lines)
                elif current_system and (line.startswith('  ') or line.startswith('\t')):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # This is a planet line, format: Name: UWP [Trade Codes] [Bases] Remarks
                    planet_parts = line.split(':', 1)
                    if len(planet_parts) >= 2:
                        planet_name = planet_parts[0].strip()
                        planet_data = line[len(planet_name):].strip()
                        
                        # Extract UWP (starts with a letter, contains a dash)
                        uwp_match = re.search(r'([A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?)', planet_data)
                        uwp = uwp_match.group(1) if uwp_match else '???????'
                        
                        planet_info = {
                            'name': planet_name,
                            'UWP': uwp,
                            'is_main_world': False
                        }
                        
                        # Extract trade codes in parentheses
                        trade_match = re.search(r'\(([A-Za-z0-9\s,]+)\)', planet_data)
                        if trade_match:
                            trade_codes = [tc.strip() for tc in trade_match.group(1).split(',') if tc.strip()]
                            planet_info['trade_codes'] = ', '.join(trade_codes)
                        
                        # Extract bases (N, S, X, W)
                        bases = []
                        if 'N' in planet_data:
                            bases.append('N')
                        if 'S' in planet_data:
                            bases.append('S')
                        if 'X' in planet_data:
                            bases.append('X')
                        if 'W' in planet_data:
                            bases.append('W')
                        
                        if bases:
                            planet_info['bases'] = ''.join(bases)
                        
                        # Add the planet to the current system
                        current_system['planets'].append(planet_info)
                        logger.debug(f"  Found planet: {planet_name} with UWP: {uwp}")
            
            # Add the last system if it exists
            if current_system:
                systems.append(current_system)
            
            logger.info(f"Found {len(systems)} systems in sector {sector_name}")
            
            # Process each system and its planets
            for system in systems:
                # Validate that this system should belong to this sector
                system_name = system.get('name', 'Unnamed System')
                system_hex = system.get('hex', '????')
                
                # Skip synthetic or test systems that don't belong to real sectors
                if 'Synthetic' in system_name or system_name.startswith('Test') or system_name.startswith('Debug'):
                    logger.debug(f"Skipping synthetic/test system: {system_name}")
                    continue
                
                # Create the system with proper sector linkage
                system_id = self.get_or_create_system(sector_id, system)
                
                if system_id and 'planets' in system:
                    for planet_idx, planet in enumerate(system['planets'], 1):
                        # Prepare planet data with all required fields
                        planet_uwp = planet.get('UWP', '???????')
                        system_hex = system.get('hex', '????')
                        
                        # Skip synthetic planets
                        planet_name = planet.get('name', f"{system.get('name', 'Unnamed System')} {planet_idx}")
                        if 'Synthetic' in planet_name or planet_name.startswith('Test'):
                            logger.debug(f"Skipping synthetic planet: {planet_name}")
                            continue
                        
                        full_planet_data = {
                            'name': planet_name,
                            'sector_id': sector_id,  # Critical: ensure proper sector linkage
                            'system_name': system.get('name', 'Unnamed System'),
                            'system_hex': system_hex,
                            'planet_number': planet_idx,
                            # Set default values for required fields
                            'x_coordinate': system.get('x'),
                            'y_coordinate': system.get('y'),
                            'hex': system_hex,
                            'starport': planet_uwp[0] if planet_uwp and len(planet_uwp) > 0 else 'X',
                            'size': planet_uwp[1] if planet_uwp and len(planet_uwp) > 1 else '0',
                            'atmosphere': planet_uwp[2] if planet_uwp and len(planet_uwp) > 2 else '0',
                            'hydrographics': planet_uwp[3] if planet_uwp and len(planet_uwp) > 3 else '0',
                            'population': planet_uwp[4] if planet_uwp and len(planet_uwp) > 4 else '0',
                            'government': planet_uwp[5] if planet_uwp and len(planet_uwp) > 5 else '0',
                            'law_level': planet_uwp[6] if planet_uwp and len(planet_uwp) > 6 else '0',
                            'tech_level': planet_uwp[8] if planet_uwp and len(planet_uwp) > 8 else '0',
                            'allegiance': system.get('allegiance_code', 'Na'),
                            'bases': planet.get('bases', ''),
                            'travel_code': system.get('travel_code', ''),
                            'trade_codes': planet.get('trade_codes', ''),
                            'importance': system.get('importance', ''),
                            'economic': system.get('economic', ''),
                            'stellar': system.get('stellar_data', '')
                        }
                        
                        # Add any additional fields from the planet data
                        for key, value in planet.items():
                            if key not in full_planet_data or full_planet_data[key] is None:
                                full_planet_data[key] = value
                        
                        if not self.update_or_create_planet(sector_id, full_planet_data):
                            logger.warning(f"      Failed to update/create planet {planet.get('name', 'Unnamed')}")
                        else:
                            logger.info(f"      Successfully processed planet {planet.get('name', 'Unnamed')}")
                            if planet_idx == 1:  # Only update stats for the main world
                                self.stats['planets_created'] += 1
                    
                    logger.info(f"  System: {system.get('name', 'Unnamed')} ({len(system['planets'])} planets)")
                else:
                    logger.info(f"  System: {system.get('name', 'Unnamed')} (no planets)")
            
            # Update stats for systems processed
            self.stats['systems_created'] += len(systems)
            
        except Exception as e:
            logger.error(f"Error processing systems and planets for sector {sector_name}: {e}", exc_info=True)
            self.stats['errors'] += 1

    def sync_sectors(self) -> None:
        """Main method to synchronize sectors with the Traveller Map API."""
        try:
            logger.info(f"Starting sector synchronization for milieu: {self.milieu}")
            
            # Get existing sectors
            existing_sectors = self.get_existing_sectors()
            self.stats['total_in_db'] = len(existing_sectors)
            
            # Create lookup dictionaries
            sectors_by_name = {s['name'].lower(): s for s in existing_sectors if s.get('name')}
            sectors_by_abbr = {s['abbreviation'].lower(): s for s in existing_sectors if s.get('abbreviation')}
            
            existing_sectors_dict = {
                'by_name': sectors_by_name,
                'by_abbr': sectors_by_abbr
            }
            
            # Get universe data from API
            logger.info("Fetching universe data from Traveller Map API...")
            universe_data = self.api.get_universe()
            
            if "Sectors" not in universe_data:
                logger.error("No sectors found in API response")
                return
            
            api_sectors = universe_data["Sectors"]
            self.stats['total_in_api'] = len(api_sectors)
            logger.info(f"Found {len(api_sectors)} sectors in the API")
            
            # Process each sector
            for i, api_sector in enumerate(api_sectors, 1):
                try:
                    # Process sector metadata
                    sector_info = self.process_sector(api_sector, existing_sectors_dict)
                    
                    # Update the existing_sectors_dict after processing each sector
                    if sector_info and 'name' in sector_info and 'abbreviation' in sector_info:
                        existing_sectors_dict['by_name'][sector_info['name'].lower()] = sector_info
                        existing_sectors_dict['by_abbr'][sector_info['abbreviation'].lower()] = sector_info
                    
                    # Log progress
                    if i % 5 == 0 or i == len(api_sectors):
                        logger.info(f"Processed {i}/{len(api_sectors)} sectors...")
                        
                except Exception as e:
                    sector_name = api_sector.get('Name', 'Unknown')
                    logger.error(f"Error processing sector {sector_name}: {e}", exc_info=True)
                    self.stats['errors'] += 1
            
            # Log summary
            logger.info("\nSynchronization complete!")
            logger.info(f"Total sectors in database: {self.stats['total_in_db']}")
            logger.info(f"Total sectors in API: {self.stats['total_in_api']}")
            logger.info(f"Sectors created: {self.stats['sectors_created']}")
            logger.info(f"Sectors updated: {self.stats['sectors_updated']}")
            logger.info(f"Sectors skipped: {self.stats['sectors_skipped']}")
            logger.info(f"Systems created/updated: {self.stats['systems_created']}")
            logger.info(f"Planets created: {self.stats['planets_created']}")
            logger.info(f"Planets updated: {self.stats['planets_updated']}")
            logger.info(f"Errors encountered: {self.stats['errors']}")
            
        except Exception as e:
            logger.error(f"Fatal error during synchronization: {e}", exc_info=True)
            raise

    def fix_existing_sector_ids(self):
        """Fix existing planets that have NULL sector_id by inferring from system data."""
        try:
            logger.info("Fixing existing planets with NULL sector_id...")
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Find planets with NULL sector_id
                cursor.execute("SELECT planet_id, system_name, system_hex FROM planets WHERE sector_id IS NULL")
                planets_to_fix = cursor.fetchall()
                
                if not planets_to_fix:
                    logger.info("No planets with NULL sector_id found.")
                    return
                
                logger.info(f"Found {len(planets_to_fix)} planets with NULL sector_id")
                
                # Get all sectors for matching
                cursor.execute("SELECT sector_id, name, abbreviation FROM sectors")
                sectors = cursor.fetchall()
                
                fixed_count = 0
                for planet in planets_to_fix:
                    planet_id, system_name, system_hex = planet
                    
                    # Try to match planet to a sector based on system name or hex
                    sector_id = None
                    
                    # First, try to find the system in the systems table
                    cursor.execute("SELECT sector_id FROM systems WHERE name = ? OR hex = ?", 
                                 (system_name, system_hex))
                    system_result = cursor.fetchone()
                    
                    if system_result and system_result['sector_id']:
                        sector_id = system_result['sector_id']
                    else:
                        # Fallback: assign to the first available sector for this milieu
                        cursor.execute("SELECT sector_id FROM sectors WHERE milieu = ? LIMIT 1", 
                                     (self.milieu,))
                        fallback_result = cursor.fetchone()
                        if fallback_result:
                            sector_id = fallback_result['sector_id']
                    
                    if sector_id:
                        cursor.execute("UPDATE planets SET sector_id = ? WHERE planet_id = ?", 
                                     (sector_id, planet_id))
                        fixed_count += 1
                
                conn.commit()
                logger.info(f"Fixed sector_id for {fixed_count} planets")
                
        except Exception as e:
            logger.error(f"Error fixing existing sector_ids: {e}")

def main():
    """Main entry point for the script."""
    try:
        # Initialize synchronizer with default settings
        synchronizer = SectorSynchronizer()
        
        # Start synchronization (no longer need the fix method since we cleared the data)
        synchronizer.sync_sectors()
        
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
