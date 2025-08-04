import os
import re
import time
from model.traveller_map_api_fixed_v2 import TravellerMapAPI
from model.traveller_database import TravellerDatabase
from model.sectors_db import SectorDB
from model.systems_db import SystemDB
from model.planets_db import PlanetDB
from model.relationship_db import RelationshipDB
import logging

# Set up file-based logging
logging.basicConfig(filename='/tmp/tasj_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
debug_logger = logging.getLogger('tasj_debug')

def parse_sector_info(sec_data):
    """
    Parses the header (comment lines starting with '#') from the SEC file
    to extract sector-level metadata. Returns a dictionary with keys such as:
      - name
      - abbreviation
      - milieu
      - coordinates (if available)
    """
    metadata = {}
    for line in sec_data.splitlines():
        line = line.strip()
        if not line.startswith("#"):
            continue
        # Remove the '#' and any leading spaces.
        content = line.lstrip("#").strip()
        # Look for key-value pairs separated by colon.
        if ":" in content:
            key, value = content.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            metadata[key] = value
        else:
            # If the line does not contain a colon, it could be a free-form line.
            # For example, the first non-empty line might be the sector name.
            if "name" not in metadata and content:
                # Also remove any trailing parenthesized text
                metadata["name"] = re.sub(r"\s*\(.*?\)$", "", content)
    return metadata

def parse_sec_line(line):
    """
    Parse a single SEC line using fixed-width positions.
    
    Expected positions (adjust these as needed):
       1-4   : Hex number (e.g., "0914")
       6-20  : Planet name
       21-29 : UWP (world profile)
       30    : Bases (1 char)
       32-48 : Trade codes & comments
       49-50 : Zone
       52-54 : PBG
       56-57 : Allegiance
       59-74 : Stellar data

    Returns a dictionary with keys:
      - "hex"
      - "name"
      - "UWP"
      - "bases"
      - "trade_codes"
      - "zone"
      - "PBG"
      - "allegiance"
      - "stellar"
      
    If the line is too short, returns None.
    """
    if len(line) < 74:
        return None  # not long enough for a valid line
    try:
        hex_code = line[0:4].strip()
        name = line[5:20].strip()
        # Remove trailing parenthesized text (used for allegiance hints) from the planet name
        name = re.sub(r"\s*\(.*?\)$", "", name)
        uwp = line[20:29].strip()
        bases = line[29:30].strip()  # position 30 (1 char)
        trade_codes = line[31:48].strip()
        zone = line[48:50].strip()
        pbg = line[51:54].strip()
        allegiance = line[55:57].strip()
        stellar = line[58:74].strip()
        return {
            "hex": hex_code,
            "name": name,
            "UWP": uwp,
            "bases": bases,
            "trade_codes": trade_codes,
            "zone": zone,
            "PBG": pbg,
            "allegiance": allegiance,
            "stellar": stellar
        }
    except Exception:
        return None

def create_thread_safe_db_connection(db_type):
    """Create a new database connection that's safe to use in worker threads."""
    # Create a new instance bypassing the singleton pattern
    db_instance = object.__new__(TravellerDatabase)
    db_instance._initialized = False
    db_instance.__init__(db_type)
    return db_instance

def download_data_task(db_type, progress_queue, cancel_event):
    """Background task for downloading sector and planet data."""
    db_instance = create_thread_safe_db_connection(db_type)
    sector_db = SectorDB(db_instance)
    planet_db = PlanetDB(db_instance)
    system_db = SystemDB(db_instance)
    relationship_db = RelationshipDB(db_instance)
    api = TravellerMapAPI()

    # Define constants for repeated messages
    CANCEL_MSG = "⏹️ Download cancelled by user."
    
    # Initialize variables
    processed_sectors = 0
    total_planets = 0
    try:
        universe_json = api.get_universe()
        if not (isinstance(universe_json, dict) and "Sectors" in universe_json):
            progress_queue.put((0, "❌ Error: Universe data does not contain 'Sectors'."))
            return

        sectors_json = universe_json["Sectors"]
        progress_queue.put((0, f"✅ Retrieved {len(sectors_json)} sectors."))

        for idx, sector_obj in enumerate(sectors_json):
            if cancel_event.is_set():
                progress_queue.put((0, CANCEL_MSG))
                return

            # Try to get the sector name from the object first.
            official_name = sector_obj.get("Name", "").strip() or sector_obj.get("Abbreviation", "").strip()
            if not official_name:
                progress_queue.put((0, "⚠️ Skipping sector due to missing name/abbreviation."))
                continue

            # Retrieve the SEC data for the sector.
            raw_sec = api.get_sector_sec(official_name)

            # Use the header lines to extract additional sector info.
            sector_metadata = parse_sector_info(raw_sec)
            # Prefer the explicit "name" from the metadata; otherwise, use the official name.
            sector_name = sector_metadata.get("name", official_name)

            progress_queue.put((0, f"🛰️ Processing sector: {sector_name}"))

            # Upsert the sector record. You can add additional fields from sector_metadata if desired.
            sector_data = {"name": sector_name}
            if "abbreviation" in sector_metadata:
                sector_data["abbreviation"] = sector_metadata["abbreviation"]
            if "milieu" in sector_metadata:
                sector_data["milieu"] = sector_metadata["milieu"]
            sector_db.upsert_sector(sector_data)
            
            # Get the sector record to get the sector_id for foreign key relationships
            sector_record = sector_db.get_sector_by_name(sector_name)
            if not sector_record:
                progress_queue.put((0, f"❌ Error: Could not retrieve sector record for '{sector_name}' after upsert."))
                continue
            sector_id = sector_record[0]  # First column is sector_id
            progress_queue.put((0, f"DEBUG: Retrieved sector_id {sector_id} for sector '{sector_name}'"))

            # Split the SEC file into lines and filter candidate planet lines.
            lines = raw_sec.splitlines()
            planet_lines = [
                line for line in lines
                if line.strip() and not line.strip().startswith("#") and re.match(r"^\d{4}", line)
            ]

            if not planet_lines:
                progress_queue.put((0, f"  DEBUG: No planet lines matched for sector '{sector_name}'. Raw SEC data:"))
                for line in lines:
                    progress_queue.put((0, f"    DEBUG: {line}"))
                progress_queue.put((0, f"\n✅ Successfully updated sector '{sector_name}'."))
                continue

            # Parse each candidate planet line.
            planets = [parse_sec_line(line) for line in planet_lines]
            planets = [planet for planet in planets if planet]

            # Group planets by hex coordinate to handle systems
            systems_data = {}
            for planet in planets:
                hex_coord = planet.get("hex", "0000")
                if hex_coord not in systems_data:
                    systems_data[hex_coord] = {
                        "hex": hex_coord,
                        "name": planet.get("name", f"System {hex_coord}"),
                        "sector_id": sector_id,
                        "planets": []
                    }
                systems_data[hex_coord]["planets"].append(planet)

            sector_planets = 0
            progress_queue.put((0, f"INFO: Starting system/planet processing for sector {sector_name} ({len(systems_data)} systems, {len(planets)} planets)..."))
            
            for hex_coord, system_data in systems_data.items():
                if cancel_event.is_set():
                    progress_queue.put((0, CANCEL_MSG))
                    return

                # Create/update the system record
                system_record = {
                    "name": system_data["name"],
                    "hex": hex_coord,
                    "sector_id": sector_id
                }
                
                # Process system and its planets using the model layer
                try:
                    # Create a system record with the necessary data
                    system_record = {
                        "name": system_data["name"],
                        "hex": hex_coord,
                        "sector_id": sector_id
                    }
                    
                    # Process the system and its planets in the model layer with relationship handling
                    result = system_db.process_system_with_planets(
                        system_record, 
                        system_data["planets"], 
                        planet_db,
                        relationship_db
                    )
                    
                    if result["success"]:
                        # Log system update
                        debug_logger.info(f"Sending system update to queue for {system_data['name']}")
                        # Make system messages stand out with clear prefix and separator line
                        progress_queue.put((0, "----------------------------------------"))
                        system_msg = f"SYSTEM: {system_data['name']} ({hex_coord}) with {len(system_data['planets'])} planets"
                        debug_logger.info(f"Message content: '{system_msg}'")
                        progress_queue.put((0, system_msg))
                        progress_queue.put((0, "----------------------------------------"))
                        
                        # Log relationship updates
                        if result["relationships"]["sector_system_added"]:
                            progress_queue.put((0, "        LINK: Sector-System relationship established"))
                            
                        if result["relationships"]["system_planets_added"] > 0:
                            progress_queue.put((0, "        LINK: {} System-Planet relationships established".format(
                                result['relationships']['system_planets_added'])))
                        
                        # Log planet updates
                        for planet in system_data["planets"]:
                            if cancel_event.is_set():
                                progress_queue.put((0, CANCEL_MSG))
                                return
                                
                            planet_name = planet.get('name', 'N/A')
                            planet_hex = planet.get('hex', 'N/A')
                            progress_queue.put((0, "- - - - - - - - - - - - - - - - - - - -"))
                            planet_msg = f"PLANET: {planet_name} ({planet_hex})"
                            debug_logger.info(f"Sending planet update to queue: '{planet_msg}'")
                            progress_queue.put((0, planet_msg))
                            progress_queue.put((0, "- - - - - - - - - - - - - - - - - - - -"))
                            
                        # Update planet count
                        sector_planets += result["planets_updated"]
                        
                        # Log any failures
                        if result["planets_failed"] > 0:
                            progress_queue.put((0, "        WARNING: Failed to update {} planets in this system".format(result['planets_failed'])))
                            
                        if result["relationships"]["system_planets_failed"] > 0:
                            progress_queue.put((0, "        WARNING: Failed to establish {} System-Planet relationships".format(result['relationships']['system_planets_failed'])))
                    else:
                        # Log the error
                        progress_queue.put((0, "    ERROR: Failed to process system {}: {}".format(
                            system_data['name'], result.get('error', 'Unknown error'))))
                        continue
                        
                except Exception as system_error:
                    progress_queue.put((0, "    ERROR: Failed to process system {}: {}".format(
                        system_data['name'], str(system_error))))
                    continue

            progress_queue.put((0, f"INFO: Finished planet processing loop for sector {sector_name}.")) 
            progress_queue.put((0, "✅ Processed {} planets for sector '{}'".format(sector_planets, sector_name)))
            total_planets += sector_planets
            processed_sectors += 1

        progress_queue.put((0, "✅ Download complete! Processed {} planets across {} sectors.".format(total_planets, processed_sectors)))

    except Exception as error:
        progress_queue.put((0, "❌ Error downloading data: {}".format(error)))
    finally:
        db_instance.close()
        progress_queue.put((0, "🔌 Database connection closed."))
