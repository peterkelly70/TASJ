#!/usr/bin/env python3
"""
Traveller Map API Downloader - Working Example
This script demonstrates how to properly download data from the Traveller Map API.
"""

import os
import sys
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple, List
import urllib.parse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TravellerMapDownloader:
    """A robust implementation of the Traveller Map API downloader."""
    
    BASE_URL = "https://travellermap.com"
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".traveller_map_cache")
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, base_url=None, milieu="M1105"):
        """
        Initialize the Traveller Map API downloader.
        
        Args:
            base_url: Optional custom base URL (defaults to https://travellermap.com)
            milieu: Default milieu code to use (defaults to M1105)
        """
        self.base_url = base_url or self.BASE_URL
        self.base_url = self.base_url.rstrip('/')
        self.milieu = milieu
        self.ensure_cache_dir()
        
    def ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.CACHE_DIR):
            try:
                os.makedirs(self.CACHE_DIR)
                logger.info(f"Created cache directory: {self.CACHE_DIR}")
            except Exception as e:
                logger.error(f"Failed to create cache directory: {e}")
                return False
        return True
        
    def get_cache_path(self, url):
        """Generate a cache file path for a URL."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Use appropriate extension based on URL path
        if url.endswith(('.png', '.jpg', '.jpeg')):
            extension = os.path.splitext(url)[1]
        elif '/image' in url or '/poster' in url or '/jumpmap' in url or '/tile' in url:
            extension = '.png'
        else:
            extension = '.json'
            
        return os.path.join(self.CACHE_DIR, f"{url_hash}{extension}")

    def _make_api_request(self, endpoint, params=None, use_api_prefix=True):
        """
        Make a request to the Traveller Map API with proper error handling.
        
        Args:
            endpoint: API endpoint path (without leading slash)
            params: Dictionary of query parameters
            use_api_prefix: Whether to use /api/ prefix (True) or /data/ prefix (False)
            
        Returns:
            Response object from requests
        """
        # Build the URL
        prefix = "/api/" if use_api_prefix else "/data/"
        url = f"{self.base_url}{prefix}{endpoint}"
        
        # Add parameters
        params = params or {}
        
        # Add milieu if not already in params
        if 'milieu' not in params and self.milieu:
            params['milieu'] = self.milieu
            
        # Log the request
        param_str = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        full_url = f"{url}?{param_str}" if param_str else url
        logger.info(f"Making API request to: {full_url}")
        
        # Check cache first
        cache_path = self.get_cache_path(full_url)
        if os.path.exists(cache_path):
            logger.info(f"Loading from cache: {cache_path}")
            with open(cache_path, 'rb') as f:
                content = f.read()
                if content:
                    # For JSON data, we need to decode it
                    if cache_path.endswith('.json'):
                        return json.loads(content.decode('utf-8'))
                    return content
        
        # Make the request with retry logic
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                # Cache the response
                if self.ensure_cache_dir():
                    with open(cache_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Cached response to: {cache_path}")
                
                # Return appropriate type based on content
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.json()
                return response.content
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                retry_count += 1
                if retry_count < self.MAX_RETRIES:
                    logger.info(f"Retrying in {self.RETRY_DELAY} seconds... (attempt {retry_count+1}/{self.MAX_RETRIES})")
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts")
                    raise
    
    # -------------------------
    # Universe Data
    # -------------------------
    def get_universe(self, milieu=None):
        """
        Get the universe data.
        
        Args:
            milieu: Optional milieu code to override the default
            
        Returns:
            Dictionary containing universe data with sectors list
        """
        params = {}
        if milieu:
            params['milieu'] = milieu
            
        return self._make_api_request("", params, use_api_prefix=False)
    
    # -------------------------
    # Sector Data
    # -------------------------
    def get_sector_data(self, sector_name, milieu=None):
        """
        Get comprehensive data for a sector.
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code to override the default
            
        Returns:
            Dictionary containing sector data with metadata and systems
        """
        # First get the metadata
        metadata = self.get_sector_metadata(sector_name, milieu)
        
        # Then get the systems data in T5 format
        t5_data = self.get_sector_t5(sector_name, milieu)
        
        # Parse the T5 data into systems
        systems = self._parse_t5_systems(t5_data)
        
        # Combine the data
        return {
            "metadata": metadata,
            "systems": systems
        }
    
    def get_sector_metadata(self, sector_name, milieu=None):
        """
        Get metadata for a sector.
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code to override the default
            
        Returns:
            Dictionary containing sector metadata
        """
        params = {'sector': sector_name}
        if milieu:
            params['milieu'] = milieu
            
        return self._make_api_request("metadata", params)
    
    def get_sector_t5(self, sector_name, milieu=None):
        """
        Get sector data in T5 format.
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code to override the default
            
        Returns:
            String containing T5 format data
        """
        params = {'sector': sector_name}
        if milieu:
            params['milieu'] = milieu
            
        # This returns raw text, not JSON
        response = self._make_api_request("sector", params, use_api_prefix=False)
        if isinstance(response, bytes):
            return response.decode('utf-8')
        return response
    
    def get_sector_sec(self, sector_name, milieu=None):
        """
        Get sector data in SEC format.
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code to override the default
            
        Returns:
            String containing SEC format data
        """
        params = {'sector': sector_name}
        if milieu:
            params['milieu'] = milieu
            
        # This returns raw text, not JSON
        response = self._make_api_request("sec", params, use_api_prefix=True)
        if isinstance(response, bytes):
            return response.decode('utf-8')
        return response
    
    def _parse_t5_systems(self, t5_data):
        """
        Parse T5 format data into a list of system dictionaries.
        
        Args:
            t5_data: String containing T5 format data
            
        Returns:
            List of dictionaries, each representing a system
        """
        systems = []
        current_header = None
        
        for line in t5_data.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('@'):
                # This is a header line
                current_header = line[1:].strip()
                continue
                
            if self._is_system_line(line):
                # This is a system data line
                system = self._parse_system_line(line)
                if system:
                    systems.append(system)
                    
        return systems
    
    def _is_system_line(self, line):
        """Check if a line represents a system (starts with hex code)."""
        import re
        # Match lines that start with a hex code (e.g., "0101")
        return bool(re.match(r'^[0-9A-Fa-f]{4}', line))
    
    def _parse_system_line(self, line):
        """Parse a single system line from T5 data."""
        tokens = line.split()
        if len(tokens) < 2:
            return None
            
        # Basic system data
        system = {
            'hex': tokens[0],
            'name': tokens[1],
        }
        
        # UPP code if available (position 2)
        if len(tokens) > 2:
            system['upp'] = tokens[2]
            
        # Additional data if available
        if len(tokens) > 3:
            system['raw_data'] = ' '.join(tokens[3:])
            
        return system
    
    # -------------------------
    # Image APIs
    # -------------------------
    def get_sector_image(self, sector_name, options=None, milieu=None):
        """
        Get a sector map image.
        
        Args:
            sector_name: Name or abbreviation of the sector
            options: Dictionary of options for the image (style, scale, etc.)
            milieu: Optional milieu code to override the default
            
        Returns:
            Binary image data
        """
        params = {'sector': sector_name}
        if milieu:
            params['milieu'] = milieu
            
        # Add any options
        if options:
            params.update(options)
            
        return self._make_api_request("poster", params)
    
    def get_system_image(self, sector_name, hex_code, options=None, milieu=None):
        """
        Get a system map image.
        
        Args:
            sector_name: Name or abbreviation of the sector
            hex_code: Hex code of the system (e.g. "1910")
            options: Dictionary of options for the image
            milieu: Optional milieu code to override the default
            
        Returns:
            Binary image data
        """
        params = {
            'sector': sector_name,
            'hex': hex_code
        }
        if milieu:
            params['milieu'] = milieu
            
        # Add any options
        if options:
            params.update(options)
            
        return self._make_api_request("jumpmap", params)
    
    # -------------------------
    # Search API
    # -------------------------
    def search(self, query, milieu=None):
        """
        Search for worlds, sectors, etc.
        
        Args:
            query: Search query string
            milieu: Optional milieu code to override the default
            
        Returns:
            Search results as a dictionary
        """
        params = {'q': query}
        if milieu:
            params['milieu'] = milieu
            
        return self._make_api_request("search", params)
    
    # -------------------------
    # Available Milieux
    # -------------------------
    def get_available_milieux(self):
        """
        Get a list of available milieux.
        
        Returns:
            List of milieu objects with 'Code' and 'Name' properties
        """
        return self._make_api_request("milieux")


def save_image_file(image_data, filename):
    """Save binary image data to a file."""
    with open(filename, 'wb') as f:
        f.write(image_data)
    logger.info(f"Saved image to: {filename}")
    return os.path.abspath(filename)


def main():
    """Main function to demonstrate the API downloader."""
    # Create the downloader
    api = TravellerMapDownloader()
    
    # Test sector to download
    sector_name = "Spinward Marches"
    print(f"\n=== DOWNLOADING DATA FOR {sector_name} ===\n")
    
    try:
        # Get sector metadata
        print("Downloading sector metadata...")
        metadata = api.get_sector_metadata(sector_name)
        print(f"Sector metadata: {json.dumps(metadata, indent=2)[:500]}...\n")
        
        # Get sector systems
        print("Downloading sector systems data...")
        sector_data = api.get_sector_data(sector_name)
        print(f"Found {len(sector_data['systems'])} systems in {sector_name}")
        if sector_data['systems']:
            print(f"First system: {json.dumps(sector_data['systems'][0], indent=2)}\n")
        
        # Download sector image
        print("Downloading sector map image...")
        image_options = {
            'style': 'poster',
            'scale': 64,
            'border': 1
        }
        image_data = api.get_sector_image(sector_name, image_options)
        image_path = save_image_file(image_data, f"{sector_name.replace(' ', '_')}_map.png")
        print(f"Sector map saved to: {image_path}\n")
        
        # Get a specific system image
        system_hex = "1910"  # Regina
        print(f"Downloading system map for hex {system_hex}...")
        system_image = api.get_system_image(sector_name, system_hex, {'jump': 4})
        system_path = save_image_file(system_image, f"{sector_name.replace(' ', '_')}_{system_hex}_map.png")
        print(f"System map saved to: {system_path}\n")
        
        # Search for a world
        search_term = "Regina"
        print(f"Searching for '{search_term}'...")
        search_results = api.search(search_term)
        print(f"Search results: {json.dumps(search_results, indent=2)[:500]}...\n")
        
        print("All operations completed successfully!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
