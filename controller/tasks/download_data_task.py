import os
import re
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Iterable
import requests
from model.traveller_map_api import TravellerMapAPI
from model.traveller_database import TravellerDatabase
from model.sectors_db import SectorDB
from model.planets_db import PlanetDB

FAILURE_LOG_PATH = Path("logs/sector_failures.json")

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
    Parse a single SEC line using the correct fixed-width positions.
    
    Actual SEC format positions:
       1-14  : System name
       15-18 : Hex coordinates (e.g., "0101")
       20-28 : UWP (Universal World Profile)
       30    : Bases (1 char)
       32-47 : Trade codes & comments
       49    : Zone
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
    if len(line) < 28:
        return None  # not long enough for a valid line
    try:
        # Parse according to actual SEC format
        name = line[0:14].strip()
        hex_code = line[14:18].strip()
        uwp = line[19:28].strip() if len(line) > 19 else ""
        
        # Optional fields (may not be present in shorter lines)
        bases = line[29:30].strip() if len(line) > 29 else ""
        trade_codes = line[31:47].strip() if len(line) > 31 else ""
        zone = line[48:49].strip() if len(line) > 48 else ""
        pbg = line[51:54].strip() if len(line) > 51 else ""
        allegiance = line[55:57].strip() if len(line) > 55 else ""
        stellar = line[58:74].strip() if len(line) > 58 else ""
        
        # Remove trailing parenthesized text from the planet name
        name = re.sub(r"\s*\(.*?\)$", "", name)
        
        return {
            "hex": hex_code,
            "name": name,
            "UWP": uwp,
            "bases": bases,
            "trade_codes": trade_codes,
            "travel_zone": zone,  # Use correct column name from database schema
            "pbg": pbg,
            "allegiance": allegiance,
            "stellar": stellar
        }
    except Exception as e:
        # Log the error and return None
        print(f"Error parsing UPP: {str(e)}")
        return None

def parse_hex_coordinates(hex_code: str) -> tuple[Optional[int], Optional[int]]:
    """Convert a Traveller hex string (e.g., '0101') into numeric coordinates."""
    hex_code = (hex_code or "").strip()
    if len(hex_code) != 4 or not hex_code.isdigit():
        return None, None
    try:
        return int(hex_code[:2]), int(hex_code[2:])
    except ValueError:
        return None, None


def extract_uwp_components(uwp: str) -> dict[str, str]:
    """Break a UWP string into its component fields."""
    if not uwp:
        return {}

    sanitized = uwp.strip().upper().replace('-', '')
    if not sanitized:
        return {}

    fields = {}
    mapping = [
        ("starport", 0),
        ("size", 1),
        ("atmosphere", 2),
        ("hydrographics", 3),
        ("population", 4),
        ("government", 5),
        ("law_level", 6),
    ]

    for key, index in mapping:
        if len(sanitized) > index:
            fields[key] = sanitized[index]

    if len(sanitized) > 7:
        fields["tech_level"] = sanitized[7]

    return fields


def parse_t5_tab(tab_data: str) -> Dict[str, Dict[str, str]]:
    """Parse Travellermap TAB format into a dict keyed by hex coordinates."""
    entries: Dict[str, Dict[str, str]] = {}
    if not tab_data:
        return entries

    lines = [line for line in tab_data.splitlines() if line and not line.startswith('#')]
    if not lines:
        return entries

    header = [col.strip() for col in lines[0].split('\t')]
    for line in lines[1:]:
        cols = line.split('\t')
        # Pad columns to header length to avoid IndexError
        if len(cols) < len(header):
            cols.extend([''] * (len(header) - len(cols)))
        row = {header[i]: cols[i].strip() for i in range(min(len(header), len(cols)))}
        hex_code = row.get('Hex', '').strip()
        if hex_code:
            entries[hex_code] = row

    return entries


def record_sector_failure(sector_name: str, reason: str) -> None:
    FAILURE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "sector": sector_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    try:
        if FAILURE_LOG_PATH.exists():
            with FAILURE_LOG_PATH.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    data = [item for item in data if item.get("sector") != sector_name]
                else:
                    data = []
        else:
            data = []
        data.append(entry)
        with FAILURE_LOG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        # Failure logging should never break the download
        pass


def clear_sector_failure(sector_name: str) -> None:
    if not FAILURE_LOG_PATH.exists():
        return
    try:
        with FAILURE_LOG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            return
        new_data = [item for item in data if item.get("sector") != sector_name]
        with FAILURE_LOG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(new_data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass

def download_data_task(
    db_type,
    progress_queue,
    cancel_event,
    target_sectors: Optional[Iterable[str]] = None,
    skip_existing: bool = True,
):
    """Background task for downloading sector and planet data."""
    def emit(message: str, progress: Optional[int] = None):
        progress_queue.put((progress, message))

    emit("🚀 Starting data download task...", 0)
    
    db_instance = None
    
    try:
        emit("📊 Initializing database connection...", 0)
        db_instance = TravellerDatabase(db_type)
        emit("✅ Database connection established.")
        
        sector_db = SectorDB(db_instance)
        planet_db = PlanetDB(db_instance)
        if skip_existing is None:
            skip_existing = os.getenv("TASJ_SKIP_EXISTING_SECTORS", "true").lower() in {"1", "true", "yes", "y"}
        
        emit("🌐 Initializing API connection...")
        api = TravellerMapAPI()
        emit("✅ API connection initialized.")
        
        total_planets = 0
        emit("🔍 Fetching universe data from API...")
        try:
            universe_json = api.get_universe()
            emit("✅ Universe data retrieved successfully.")
        except Exception as api_error:
            emit(f"❌ Error fetching universe data: {str(api_error)}")
            import traceback
            emit(f"DEBUG: {traceback.format_exc()}")
            return
            
        if not isinstance(universe_json, dict):
            emit(f"❌ Error: Universe data is not a dictionary. Got {type(universe_json).__name__} instead.")
            emit(f"DEBUG: Universe data content: {str(universe_json)[:500]}...")
            return
            
        if "Sectors" not in universe_json:
            emit("❌ Error: Universe data does not contain 'Sectors' key.")
            emit(f"DEBUG: Available keys: {', '.join(universe_json.keys())}")
            return
            
        if not isinstance(universe_json["Sectors"], list):
            emit(f"❌ Error: Sectors data is not a list. Got {type(universe_json['Sectors']).__name__} instead.")
            return

        sectors_json = universe_json["Sectors"]

        target_lookup = None
        if target_sectors:
            target_lookup = {value.lower() for value in target_sectors if isinstance(value, str)}

        filtered_sectors = []
        for sector_obj in sectors_json:
            if target_lookup:
                names = set()
                name = sector_obj.get("Name", "").strip()
                abbr = sector_obj.get("Abbreviation", "").strip()
                if name:
                    names.add(name.lower())
                if abbr:
                    names.add(abbr.lower())
                if not names & target_lookup:
                    continue
            filtered_sectors.append(sector_obj)

        if target_lookup and not filtered_sectors:
            emit("⚠️ No matching sectors found; defaulting to full download.")
            filtered_sectors = sectors_json

        if not filtered_sectors:
            filtered_sectors = sectors_json

        total_sectors = len(filtered_sectors)
        emit(f"✅ Retrieved {total_sectors} sectors.")

        # Debug: Print first few sectors to help diagnose issues
        if sectors_json:
            emit("DEBUG: First sector data sample:")
            first_sector = sectors_json[0]
            for key, value in first_sector.items():
                emit(f"DEBUG: {key}: {str(value)[:100]}")

        total_sectors = max(total_sectors, 1)

        for idx, sector_obj in enumerate(filtered_sectors, start=1):
            if cancel_event.is_set():
                emit("⏹️ Download cancelled by user.", 100)
                return

            # Try to get the sector name from the object first.
            official_name = sector_obj.get("Name", "").strip() or sector_obj.get("Abbreviation", "").strip()
            if not official_name:
                emit("⚠️ Skipping sector due to missing name/abbreviation.")
                continue

            existing_sector = sector_db.get_sector_by_name(official_name)
            existing_sector_id = existing_sector[0] if existing_sector else None

            progress = int(((idx - 1) / total_sectors) * 100)
            if skip_existing and existing_sector_id:
                existing_planets = planet_db.count_planets_for_sector(existing_sector_id)
                if existing_planets > 0:
                    emit(
                        f"ℹ️ Skipping sector '{official_name}' (already has {existing_planets} planets).",
                        progress,
                    )
                    continue

            # Retrieve datasets for the sector.
            try:
                raw_sec = api.get_sector_sec(official_name)
            except requests.HTTPError as http_err:
                emit(f"WARNING: Skipping sector '{official_name}' due to SEC download error: {http_err}")
                record_sector_failure(official_name, str(http_err))
                continue
            except Exception as generic_err:
                emit(f"ERROR: Unexpected SEC download error for '{official_name}': {generic_err}")
                record_sector_failure(official_name, str(generic_err))
                continue

            try:
                raw_tab = api.get_sector_tab(official_name)
                tab_entries = parse_t5_tab(raw_tab)
            except requests.HTTPError as tab_http_err:
                emit(f"WARNING: TAB data unavailable for '{official_name}': {tab_http_err}")
                record_sector_failure(official_name, str(tab_http_err))
                tab_entries = {}
            except Exception as tab_error:
                emit(f"ERROR: Failed to parse TAB data for '{official_name}': {tab_error}")
                record_sector_failure(official_name, str(tab_error))
                tab_entries = {}

            # Use the header lines to extract additional sector info.
            sector_metadata = parse_sector_info(raw_sec)
            # Prefer the explicit "name" from the metadata; otherwise, use the official name.
            sector_name = sector_metadata.get("name", official_name)

            # If parsed name differs, perform skip check again if requested
            if skip_existing and sector_name != official_name:
                alt_sector = sector_db.get_sector_by_name(sector_name)
                alt_sector_id = alt_sector[0] if alt_sector else None
                if alt_sector_id:
                    existing_planets = planet_db.count_planets_for_sector(alt_sector_id)
                    if existing_planets > 0:
                        emit(
                            f"ℹ️ Skipping sector '{sector_name}' (already has {existing_planets} planets).",
                            progress,
                        )
                        continue

            emit(f"🛰️ Processing sector: {sector_name}", progress)

            # Upsert the sector record. You can add additional fields from sector_metadata if desired.
            sector_data = {"name": sector_name}
            if "abbreviation" in sector_metadata:
                sector_data["abbreviation"] = sector_metadata["abbreviation"]
            if "milieu" in sector_metadata:
                sector_data["milieu"] = sector_metadata["milieu"]
            sector_id = sector_db.upsert_sector(sector_data)
            if sector_id is None:
                emit(f"ERROR: Failed to persist sector '{sector_name}'. Skipping.")
                continue

            # Split the SEC file into lines and filter candidate system lines.
            lines = raw_sec.splitlines()
            
            # Find actual system data lines - they come after the format description
            # and contain system name + hex coordinates + UWP data
            in_data_section = False
            system_lines = []
            
            for line in lines:
                # Skip header comments and format descriptions
                if line.strip().startswith('#') or not line.strip():
                    continue
                    
                # Look for the end of format descriptions (contains ruler or "Stellar Data")
                if 'Stellar Data' in line or '....+....1....+....2' in line:
                    in_data_section = True
                    continue
                    
                # Skip format description lines
                if ':' in line and ('Name' in line or 'HexNbr' in line or 'UWP' in line):
                    continue
                    
                # If we're in the data section and line has proper length, it's likely system data
                if in_data_section and len(line) >= 28:
                    # Verify it looks like system data (has name and hex pattern)
                    name_part = line[0:14].strip()
                    hex_part = line[14:18].strip()
                    if name_part and re.match(r'^\d{4}$', hex_part):
                        system_lines.append(line)
            
            planet_lines = system_lines

            if not planet_lines:
                emit(f"DEBUG: No planet lines matched for sector '{sector_name}'. Raw SEC data:")
                for line in lines[:5]:  # Show first 5 lines for debugging
                    emit(f"DEBUG: {line}")
                emit(f"✅ Processed 0 planets for sector '{sector_name}'.")
                continue

            # Parse each candidate planet line.
            planets = [parse_sec_line(line) for line in planet_lines]
            planets = [planet for planet in planets if planet]

            sector_planets = 0
            emit(f"INFO: Starting planet processing loop for sector {sector_name} ({len(planets)} planets)...")
            for planet_index, planet in enumerate(planets):
                if cancel_event.is_set():
                    emit("⏹️ Download cancelled by user.", 100)
                    return

                # Set a default image path if not provided.
                if "image_path" not in planet or not planet["image_path"]:
                    planet["image_path"] = "default_planet.png"

                planet_name = planet.get('name', '').strip() or 'Unknown'
                planet_hex = planet.get('hex', '').strip()

                planet_record = {
                    "name": planet_name,
                    "sector_id": sector_id,
                    "hex": planet_hex,
                    "UWP": planet.get('UWP', ''),
                    "bases": planet.get('bases', ''),
                    "trade_codes": planet.get('trade_codes', ''),
                    "travel_zone": planet.get('travel_zone', ''),
                    "allegiance": planet.get('allegiance', ''),
                    "stellar": planet.get('stellar', ''),
                    "pbg": planet.get('pbg', ''),
                    "image_path": planet.get('image_path', 'default_planet.png'),
                }

                tab_row = tab_entries.get(planet_hex)
                if tab_row:
                    planet_record["bases"] = tab_row.get('Bases', planet_record["bases"])
                    planet_record["trade_codes"] = tab_row.get('Remarks', planet_record["trade_codes"])
                    zone_value = tab_row.get('Zone', '')
                    if zone_value:
                        planet_record["travel_zone"] = zone_value
                        planet_record["travel_code"] = zone_value
                    planet_record["allegiance"] = tab_row.get('Allegiance', planet_record["allegiance"])
                    planet_record["stellar"] = tab_row.get('Stars', planet_record["stellar"])
                    planet_record["pbg"] = tab_row.get('PBG', planet_record["pbg"])
                    planet_record["importance"] = tab_row.get('Ix', '')
                    planet_record["economic"] = tab_row.get('Ex', '')
                    planet_record["subsector_id"] = tab_row.get('Subsector', '')
                    planet_record["UWP"] = tab_row.get('UWP', planet_record["UWP"])
                    planet_record["name"] = tab_row.get('Name', planet_record["name"])

                pbg_value = planet_record.get("pbg", "")
                if pbg_value and len(pbg_value) >= 3:
                    planet_record["gas_giant"] = 'Y' if pbg_value[2] != '0' else 'N'

                planet_record.setdefault("importance", "")
                planet_record.setdefault("economic", "")
                planet_record.setdefault("travel_code", planet_record.get("travel_zone", ""))
                planet_record.setdefault("gas_giant", "")
                planet_record.setdefault("subsector_id", "")

                x_coord, y_coord = parse_hex_coordinates(planet_hex)
                if x_coord is not None and y_coord is not None:
                    planet_record["x_coordinate"] = x_coord
                    planet_record["y_coordinate"] = y_coord

                uwp_fields = extract_uwp_components(planet_record["UWP"])
                planet_record.update(uwp_fields)

                emit(f"DEBUG: Upserting planet {planet_index + 1}/{len(planets)}: {planet_name} ({planet_hex})...")
                try:
                    success = planet_db.upsert_planet(planet_record)
                    if success:
                        emit(f"DEBUG: Upserted planet {planet_name} ({planet_hex}).")
                    else:
                        emit(f"ERROR: Database reported failure upserting {planet_name} ({planet_hex}).")
                except Exception as upsert_error:
                    emit(f"ERROR: Failed to upsert planet {planet_name} ({planet_hex}): {upsert_error}")
                    # Decide if you want to continue with other planets or stop
                    # continue 
                sector_planets += 1

            emit(f"INFO: Finished planet processing loop for sector {sector_name}.")
            emit(f"✅ Processed {sector_planets} planets for sector '{sector_name}'.")
            clear_sector_failure(official_name)
            if sector_name != official_name:
                clear_sector_failure(sector_name)
            total_planets += sector_planets

        emit(f"🎉 Download complete: {total_planets} planets updated.", 100)

    except Exception as ex:
        # Handle any errors that occur during the download process.
        emit(f"Error downloading data: {str(ex)}")
        import traceback
        emit(f"DEBUG: {traceback.format_exc()}")
    finally:
        if db_instance:
            db_instance.close()
        emit("🔌 Database connection closed.", 100)
