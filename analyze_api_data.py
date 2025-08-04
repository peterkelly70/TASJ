#!/usr/bin/env python3
"""
Script to download and analyze Traveller Map API data.
This will fetch data from various endpoints and save the responses to files for analysis.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://travellermap.com"
OUTPUT_DIR = "api_analysis"
SECTOR_NAME = "Spinward Marches"  # A well-known sector for testing
SYSTEM_HEX = "1910"  # Regina system in Spinward Marches
MILIEU = "M1105"  # Default milieu

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

def save_response(endpoint_name: str, data: Any, is_binary: bool = False):
    """Save API response to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine file extension
    if is_binary:
        extension = "png"
        mode = "wb"
    elif isinstance(data, (dict, list)):
        extension = "json"
        mode = "w"
    else:
        extension = "txt"
        mode = "w"
    
    filename = f"{endpoint_name}_{timestamp}.{extension}"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, mode) as f:
        if is_binary:
            f.write(data)
        elif isinstance(data, (dict, list)):
            json.dump(data, f, indent=2)
        else:
            f.write(data)
    
    logger.info(f"Saved {endpoint_name} response to {filepath}")
    return filepath

def make_api_request(endpoint: str, params: Dict[str, Any] = None, use_api_prefix: bool = True) -> Any:
    """Make a request to the Traveller Map API."""
    prefix = "/api/" if use_api_prefix else "/data/"
    url = f"{BASE_URL}{prefix}{endpoint}"
    
    logger.info(f"Requesting: {url} with params {params}")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    # Determine content type
    content_type = response.headers.get('content-type', '')
    
    if content_type.startswith('application/json'):
        return response.json()
    elif content_type.startswith('image/'):
        return response.content
    else:
        return response.text

def analyze_api_data():
    """Fetch and analyze data from various Traveller Map API endpoints."""
    ensure_output_dir()
    
    # 1. Get universe data (list of all sectors)
    logger.info("Fetching universe data...")
    universe_params = {"milieu": MILIEU}
    try:
        universe_data = make_api_request("", universe_params, use_api_prefix=False)
        save_response("universe", universe_data)
        
        # Print summary
        if "Sectors" in universe_data:
            logger.info(f"Universe data contains {len(universe_data['Sectors'])} sectors")
        else:
            logger.warning("Universe data does not contain 'Sectors' key")
    except Exception as e:
        logger.error(f"Error fetching universe data: {e}")
    
    # 2. Get sector metadata
    logger.info(f"Fetching metadata for sector: {SECTOR_NAME}")
    metadata_params = {"sector": SECTOR_NAME, "milieu": MILIEU}
    try:
        metadata = make_api_request("metadata", metadata_params)
        save_response("sector_metadata", metadata)
        
        # Print summary
        logger.info(f"Sector metadata keys: {list(metadata.keys())}")
    except Exception as e:
        logger.error(f"Error fetching sector metadata: {e}")
    
    # 3. Get sector data in T5 format
    logger.info(f"Fetching T5 data for sector: {SECTOR_NAME}")
    t5_params = {"sector": SECTOR_NAME, "milieu": MILIEU}
    try:
        t5_data = make_api_request("sector", t5_params, use_api_prefix=False)
        save_response("sector_t5", t5_data)
        
        # Print summary
        lines = t5_data.splitlines()
        logger.info(f"T5 data contains {len(lines)} lines")
        
        # Count system lines (those starting with a hex code)
        import re
        system_lines = [line for line in lines if re.match(r'^[0-9A-Fa-f]{4}', line.strip())]
        logger.info(f"T5 data contains {len(system_lines)} system entries")
    except Exception as e:
        logger.error(f"Error fetching T5 data: {e}")
    
    # 4. Get sector data in SEC format
    logger.info(f"Fetching SEC data for sector: {SECTOR_NAME}")
    sec_params = {"sector": SECTOR_NAME, "milieu": MILIEU}
    try:
        sec_data = make_api_request("sector/sec", sec_params, use_api_prefix=False)
        save_response("sector_sec", sec_data)
        
        # Print summary
        lines = sec_data.splitlines()
        logger.info(f"SEC data contains {len(lines)} lines")
    except Exception as e:
        logger.error(f"Error fetching SEC data: {e}")
    
    # 5. Get sector map image
    logger.info(f"Fetching map image for sector: {SECTOR_NAME}")
    map_params = {"sector": SECTOR_NAME, "milieu": MILIEU, "style": "poster", "scale": 64}
    try:
        map_data = make_api_request("poster", map_params)
        save_response("sector_map", map_data, is_binary=True)
        
        # Print summary
        logger.info(f"Downloaded sector map image ({len(map_data)} bytes)")
    except Exception as e:
        logger.error(f"Error fetching sector map: {e}")
    
    # 6. Get system map image
    logger.info(f"Fetching system map for {SECTOR_NAME} {SYSTEM_HEX}")
    system_map_params = {
        "sector": SECTOR_NAME,
        "hex": SYSTEM_HEX,
        "milieu": MILIEU,
        "jump": 2,
        "style": "poster"
    }
    try:
        system_map_data = make_api_request("jumpmap", system_map_params)
        save_response("system_map", system_map_data, is_binary=True)
        
        # Print summary
        logger.info(f"Downloaded system map image ({len(system_map_data)} bytes)")
    except Exception as e:
        logger.error(f"Error fetching system map: {e}")
    
    # 7. Search for a world
    search_term = "Regina"
    logger.info(f"Searching for: {search_term}")
    search_params = {"q": search_term, "milieu": MILIEU}
    try:
        search_results = make_api_request("search", search_params)
        save_response("search_results", search_results)
        
        # Print summary
        if "Results" in search_results and "Count" in search_results["Results"]:
            logger.info(f"Search returned {search_results['Results']['Count']} results")
        else:
            logger.warning("Search results do not contain expected structure")
    except Exception as e:
        logger.error(f"Error searching: {e}")
    
    # 8. Get world data
    logger.info(f"Fetching world data for {SECTOR_NAME} {SYSTEM_HEX}")
    world_params = {"sector": SECTOR_NAME, "hex": SYSTEM_HEX, "milieu": MILIEU}
    try:
        world_data = make_api_request("sec", world_params)
        save_response("world_data", world_data)
        
        # Print summary
        logger.info(f"World data keys: {list(world_data.keys())}")
    except Exception as e:
        logger.error(f"Error fetching world data: {e}")
    
    # 9. Get available milieux
    logger.info("Fetching available milieux")
    try:
        milieux_data = make_api_request("milieux")
        save_response("milieux", milieux_data)
        
        # Print summary
        if isinstance(milieux_data, list):
            logger.info(f"Found {len(milieux_data)} available milieux")
        else:
            logger.warning("Milieux data is not in expected format")
    except Exception as e:
        logger.error(f"Error fetching milieux: {e}")

    logger.info("API analysis complete. Check the output directory for results.")

if __name__ == "__main__":
    analyze_api_data()
