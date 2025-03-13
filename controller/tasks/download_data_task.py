import os
import re
import time
from model.traveller_map_api import TravellerMapAPI
from model.traveller_database import TravellerDatabase

def download_data_task(db_type, progress_queue, cancel_event):
    """ Background task for downloading sector and planet data. """
    db_instance = TravellerDatabase(db_type)  # ✅ Create a new database instance for multiprocessing
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

            official_name = sector_obj.get("Names", [{}])[0].get("Text", sector_obj.get("Abbreviation", ""))
            if not official_name:
                progress_queue.put("⚠️ Skipping sector due to missing name/abbreviation.")
                continue

            progress_queue.put(f"🛰️ Processing sector: {official_name}")

            # Retrieve SEC data for the sector.
            raw_sec = api.get_sector_sec(official_name)
            planets = [
                api.parse_sec_line(line) for line in raw_sec.splitlines() if re.match(r"^\d{4}\s", line)
            ]
            planets = [planet for planet in planets if planet]  # Remove None values

            # ✅ Process and upsert each planet record
            sector_planets = 0
            for planet in planets:
                if "image_path" not in planet or not planet["image_path"]:
                    planet["image_path"] = "default_planet.png"  # Use default image if missing

                # ✅ Check if planet exists
                existing_planet = db_instance.read_records("planets", {"name": planet["name"]})
                if existing_planet:
                    # ✅ Update existing planet
                    db_instance.update_record("planets", {
                        "x_coordinate": planet["x"],
                        "y_coordinate": planet["y"],
                        "UPP": planet.get("UPP", ""),
                        "description": planet.get("description", ""),
                        "image_path": planet.get("image_path", ""),
                        "starport": planet.get("starport", ""),
                        "size": planet.get("size", ""),
                        "atmosphere": planet.get("atmosphere", ""),
                        "hydrographics": planet.get("hydrographics", ""),
                        "population": planet.get("population", ""),
                        "government": planet.get("government", ""),
                        "law_level": planet.get("law_level", ""),
                        "tech_level": planet.get("tech_level", ""),
                        "allegiance": planet.get("allegiance", ""),
                        "stellar": planet.get("stellar", ""),
                        "gas_giant": planet.get("gas_giant", ""),
                        "bases": planet.get("bases", ""),
                        "trade_codes": planet.get("trade_codes", ""),
                        "travel_code": planet.get("travel_code", ""),
                        "importance": planet.get("importance", ""),
                        "economic": planet.get("economic", ""),
                        "hex": planet.get("hex", ""),
                    }, {"name": planet["name"]})
                else:
                    # ✅ Insert new planet
                    db_instance.create_record("planets", {
                        "name": planet["name"],
                        "x_coordinate": planet["x"],
                        "y_coordinate": planet["y"],
                        "UPP": planet.get("UPP", ""),
                        "description": planet.get("description", ""),
                        "image_path": planet.get("image_path", ""),
                        "starport": planet.get("starport", ""),
                        "size": planet.get("size", ""),
                        "atmosphere": planet.get("atmosphere", ""),
                        "hydrographics": planet.get("hydrographics", ""),
                        "population": planet.get("population", ""),
                        "government": planet.get("government", ""),
                        "law_level": planet.get("law_level", ""),
                        "tech_level": planet.get("tech_level", ""),
                        "allegiance": planet.get("allegiance", ""),
                        "stellar": planet.get("stellar", ""),
                        "gas_giant": planet.get("gas_giant", ""),
                        "bases": planet.get("bases", ""),
                        "trade_codes": planet.get("trade_codes", ""),
                        "travel_code": planet.get("travel_code", ""),
                        "importance": planet.get("importance", ""),
                        "economic": planet.get("economic", ""),
                        "hex": planet.get("hex", ""),
                    })

                sector_planets += 1

            progress_queue.put(f"✅ Processed {sector_planets} planets for sector '{official_name}'.")
            total_planets += sector_planets

        progress_queue.put(f"🎉 Download complete: {total_planets} planets updated.")

    except Exception as e:
        progress_queue.put(f"❌ Error downloading data: {e}")
    finally:
        db_instance.close_connection()
        progress_queue.put("🔌 Database connection closed." )