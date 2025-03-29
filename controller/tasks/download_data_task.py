import os
import re
import time
from model.traveller_map_api import TravellerMapAPI
from model.traveller_database import TravellerDatabase
from model.sectors_db import SectorDB
from model.planets_db import PlanetDB

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
    except Exception as e:
        return None

def download_data_task(db_type, progress_queue, cancel_event):
    """Background task for downloading sector and planet data."""
    db_instance = TravellerDatabase(db_type)
    sector_db = SectorDB(db_instance)
    planet_db = PlanetDB(db_instance)
    api = TravellerMapAPI()

    total_planets = 0
    try:
        universe_json = api.get_universe()
        if not (isinstance(universe_json, dict) and "Sectors" in universe_json):
            progress_queue.put("❌ Error: Universe data does not contain 'Sectors'.")
            return

        sectors_json = universe_json["Sectors"]
        progress_queue.put(f"✅ Retrieved {len(sectors_json)} sectors.")

        for idx, sector_obj in enumerate(sectors_json):
            if cancel_event.is_set():
                progress_queue.put("⏹️ Download cancelled by user.")
                return

            # Try to get the sector name from the object first.
            official_name = sector_obj.get("Name", "").strip() or sector_obj.get("Abbreviation", "").strip()
            if not official_name:
                progress_queue.put("⚠️ Skipping sector due to missing name/abbreviation.")
                continue

            # Retrieve the SEC data for the sector.
            raw_sec = api.get_sector_sec(official_name)

            # Use the header lines to extract additional sector info.
            sector_metadata = parse_sector_info(raw_sec)
            # Prefer the explicit "name" from the metadata; otherwise, use the official name.
            sector_name = sector_metadata.get("name", official_name)

            progress_queue.put(f"🛰️ Processing sector: {sector_name}")

            # Upsert the sector record. You can add additional fields from sector_metadata if desired.
            sector_data = {"name": sector_name}
            if "abbreviation" in sector_metadata:
                sector_data["abbreviation"] = sector_metadata["abbreviation"]
            if "milieu" in sector_metadata:
                sector_data["milieu"] = sector_metadata["milieu"]
            sector_db.upsert_sector(sector_data)

            # Split the SEC file into lines and filter candidate planet lines.
            lines = raw_sec.splitlines()
            planet_lines = [
                line for line in lines
                if line.strip() and not line.strip().startswith("#") and re.match(r"^\d{4}", line)
            ]

            if not planet_lines:
                progress_queue.put(f"DEBUG: No planet lines matched for sector '{sector_name}'. Raw SEC data:")
                for line in lines:
                    progress_queue.put(f"DEBUG: {line}")
                progress_queue.put(f"✅ Processed 0 planets for sector '{sector_name}'.")
                continue

            # Parse each candidate planet line.
            planets = [parse_sec_line(line) for line in planet_lines]
            planets = [planet for planet in planets if planet]

            sector_planets = 0
            progress_queue.put(f"INFO: Starting planet processing loop for sector {sector_name} ({len(planets)} planets)...") 
            for planet_index, planet in enumerate(planets):
                if cancel_event.is_set():
                    progress_queue.put("⏹️ Download cancelled by user.")
                    return

                # Set a default image path if not provided.
                if "image_path" not in planet or not planet["image_path"]:
                    planet["image_path"] = "default_planet.png"

                # Associate the planet with the current sector.
                planet["sector_id"] = sector_name

                # Upsert the planet record.
                planet_name = planet.get('name', 'N/A')
                planet_hex = planet.get('hex', 'N/A')
                progress_queue.put(f"DEBUG: Upserting planet {planet_index + 1}/{len(planets)}: {planet_name} ({planet_hex})...") 
                try:
                    planet_db.upsert_planet(planet)
                    progress_queue.put(f"DEBUG: Upserted planet {planet_name} ({planet_hex}).") 
                except Exception as upsert_error:
                    progress_queue.put(f"ERROR: Failed to upsert planet {planet_name} ({planet_hex}): {upsert_error}") 
                    # Decide if you want to continue with other planets or stop
                    # continue 
                sector_planets += 1

            progress_queue.put(f"INFO: Finished planet processing loop for sector {sector_name}.") 
            progress_queue.put(f"✅ Processed {sector_planets} planets for sector '{sector_name}'.")
            total_planets += sector_planets

        progress_queue.put(f"🎉 Download complete: {total_planets} planets updated.")

    except Exception as e:
        progress_queue.put(f"❌ Error downloading data: {e}")
    finally:
        db_instance.close()
        progress_queue.put("🔌 Database connection closed.")
