#!/usr/bin/env python3
"""
Updated Traveller Map API client that correctly extracts and maps data
from the Traveller Map API to the right data structures.

This implementation handles all the necessary API endpoints and properly
parses the various data formats (JSON, T5, SEC).
"""

import os
import json
import logging
import requests
import hashlib
import time
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QByteArray

# Configure logging
logger = logging.getLogger(__name__)

class TravellerMapAPI:
    """
    Traveller Map API client for accessing map data, sector information, and more.
    
    This implementation handles all the necessary API endpoints and properly
    parses the various data formats (JSON, T5, SEC).
    """
    
    # API endpoints
    BASE_URL = "https://travellermap.com"
    API_PREFIX = "/api"
    DATA_PREFIX = "/data"
    
    # Cache settings
    CACHE_DIR = os.path.join("database", "cache")
    CACHE_ENABLED = True
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, api_base_url=None, milieu="M1105", cache_dir=None):
        """
        Initialize the Traveller Map API client.
        
        Args:
            api_base_url: Optional custom base URL (defaults to https://travellermap.com)
            milieu: Default milieu code to use (defaults to M1105)
            cache_dir: Optional custom cache directory
        """
        self.api_base_url = api_base_url or self.BASE_URL
        self.api_base_url = self.api_base_url.rstrip('/')
        self.milieu = milieu
        
        if cache_dir:
            self.CACHE_DIR = cache_dir
            
        # Ensure cache directory exists
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.CACHE_DIR):
            try:
                os.makedirs(self.CACHE_DIR)
                logger.info(f"Created cache directory: {self.CACHE_DIR}")
            except Exception as e:
                logger.error(f"Failed to create cache directory: {e}")
                return False
        return True
    
    def _get_cache_path(self, endpoint: str, params: Dict[str, Any] = None, use_api_prefix: bool = True) -> str:
        """
        Generate a cache file path for an API endpoint.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            use_api_prefix: Whether to use /api/ prefix (True) or /data/ prefix (False)
            
        Returns:
            Path to the cache file
        """
        # Build the URL
        prefix = self.API_PREFIX if use_api_prefix else self.DATA_PREFIX
        url = f"{self.api_base_url}{prefix}/{endpoint}"
        
        # Create a unique hash based on URL and params
        if params:
            cache_key = f"{url}?{json.dumps(params, sort_keys=True)}"
        else:
            cache_key = url
            
        url_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Use appropriate extension based on endpoint
        if endpoint in ['poster', 'jumpmap', 'tile'] or '/image' in endpoint:
            extension = '.png'
        elif endpoint in ['sector', 'sector/sec']:
            extension = '.txt'
        else:
            extension = '.json'
            
        return os.path.join(self.CACHE_DIR, f"{url_hash}{extension}")
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any] = None, 
                         use_api_prefix: bool = True, use_cache: bool = True) -> Any:
        """
        Make a request to the Traveller Map API with proper error handling.
        
        Args:
            endpoint: API endpoint path (without leading slash)
            params: Dictionary of query parameters
            use_api_prefix: Whether to use /api/ prefix (True) or /data/ prefix (False)
            use_cache: Whether to use cache for this request
            
        Returns:
            Response data (JSON, text, or binary depending on endpoint)
            
        Raises:
            requests.HTTPError: If the API returns an error status code
            requests.RequestException: For other request failures
            ValueError: For parsing errors
        """
        # Build the URL
        prefix = self.API_PREFIX if use_api_prefix else self.DATA_PREFIX
        url = f"{self.api_base_url}{prefix}/{endpoint}"
        
        # Add parameters
        params = params or {}
        
        # Add milieu if not already in params
        if 'milieu' not in params and self.milieu:
            params['milieu'] = self.milieu
        
        # Log the request
        
    def _make_request_with_retry(self, url, params, endpoint, cache_path, cache):
        """
        Make a request with retry logic.
        
        Args:
            url: URL to request
            params: Request parameters
            endpoint: API endpoint
            cache_path: Path to cache file
            cache: Whether to use cache
            
        Returns:
            Response data
        """
        retries = 0
        while retries <= self.MAX_RETRIES:
            try:
                logger.debug(f"Requesting: {url}")
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                
                # Process and return the response
                return self._process_response(response, endpoint, cache_path, cache)
                    
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries <= self.MAX_RETRIES:
                    # Exponential backoff
                    wait_time = self.RETRY_DELAY * (2 ** (retries - 1))
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time:.1f}s ({retries}/{self.MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.MAX_RETRIES} retries: {e}")
                    raise
                    
    def _process_response(self, response, endpoint, cache_path, cache):
        """
        Process the API response.
        
        Args:
            response: Response object
            endpoint: API endpoint
            cache_path: Path to cache file
            cache: Whether to use cache
            
        Returns:
            Processed response data
        """
        content_type = response.headers.get('content-type', '')
        
        # Determine the response type
        if content_type.startswith('application/json'):
            data = response.json()
        elif content_type.startswith('image/') or endpoint in ['poster', 'jumpmap', 'tile'] or '/image' in endpoint:
            data = response.content
        else:
            data = response.text
            
        # Save to cache if enabled
        if cache:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"Cached response to: {cache_path}")
        
        return data
    
    # -----------------------------
    # Universe Endpoints
    # -----------------------------
    def get_universe(self, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the universe data (list of all sectors).
        
        Args:
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: 
            Dictionary with a "Sectors" key containing a list of sector dictionaries.
        """
        params = {}
        if milieu:
            params["milieu"] = milieu
        
        try:
            # The universe endpoint is at /api/universe, not /data
            return self._request("universe", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching universe data: {e}")
            # Return empty structure on error
            return {"Sectors": []}
    
    # -----------------------------
    # Sector Endpoints
    # -----------------------------
    def get_sector_metadata(self, sector: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves metadata for a sector.
        Endpoint: https://travellermap.com/api/metadata
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns:
            Dictionary containing sector metadata with keys like:
            - Selected: boolean
            - Tags: string
            - Abbreviation: string
            - Names: list of name objects
            - X, Y: coordinates
            - Subsectors: list of subsector objects
            - etc.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        try:
            return self._request("metadata", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching sector metadata: {e}")
            raise
    
    def get_sector_t5(self, sector: str, milieu: Optional[str] = None) -> str:
        """
        Retrieves sector data in T5 format.
        Endpoint: https://travellermap.com/data/sector
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns: 
            Text data in T5 format.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        try:
            return self._request("sector", params, use_api_prefix=False)
        except Exception as e:
            logger.error(f"Error fetching T5 data: {e}")
            raise
    
    def get_sector_sec(self, sector: str, milieu: Optional[str] = None) -> str:
        """
        Retrieves sector data in legacy SEC format.
        Endpoint: https://travellermap.com/data/sector/sec
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns: 
            Text data in SEC format.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        try:
            return self._request("sector/sec", params, use_api_prefix=False)
        except Exception as e:
            logger.error(f"Error fetching SEC data: {e}")
            raise
    
    def _parse_t5_data(self, t5_data):
        """
        Parse T5 format data into a list of system dictionaries.
        
        Args:
            t5_data: T5 format data as a string or bytes
            
        Returns:
            List of system dictionaries
        """
        systems = []
        
        # Convert bytes to string if needed
        if isinstance(t5_data, bytes):
            t5_data = t5_data.decode('utf-8')
            
        lines = t5_data.strip().split('\n')
        
        for line in lines:
            # Skip empty lines and comment lines
            if not line or line.startswith('#'):
                continue
                
            # Check if this is a system line (starts with a hex code)
            if len(line) >= 4 and line[:4].isalnum() and len(line) > 20:
                try:
                    # Parse the T5 line format
                    system = {
                        'hex': line[:4],
                        'name': line[4:19].strip() if len(line) > 19 else '',
                        'uwp': line[19:28].strip() if len(line) > 28 else '',
                    }
                    
                    # Extract additional data if available
                    if len(line) > 29:
                        system['trade_codes'] = line[29:47].strip()
                    if len(line) > 48:
                        system['travel_code'] = line[48:49].strip()
                    if len(line) > 50:
                        system['bases'] = line[50:52].strip()
                    if len(line) > 53:
                        system['zone'] = line[53:54].strip()
                    if len(line) > 55:
                        system['pbg'] = line[55:58].strip()
                    if len(line) > 59:
                        system['allegiance'] = line[59:63].strip()
                    if len(line) > 64:
                        system['stellar'] = line[64:].strip()
                        
                    systems.append(system)
                except Exception as e:
                    logger.error(f"Error parsing T5 line: {line}. Error: {e}")
                    
        return systems
    
    def get_sector_data(self, sector: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves complete sector data including metadata and system information.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns:
            Dictionary containing:
            - metadata: Sector metadata
            - systems: List of system dictionaries
        """
        try:
            # Get metadata
            metadata = self.get_sector_metadata(sector, milieu)
            
            # Get system data
            t5_data = self.get_sector_t5(sector, milieu)
            systems = self._parse_t5_data(t5_data)
            
            return {
                "metadata": metadata,
                "systems": systems
            }
            
        except Exception as e:
            logger.error(f"Error getting sector data: {e}")
            raise
    
    # -----------------------------
    # Image Endpoints
    # -----------------------------
    def get_sector_image_bytes(self, sector: str, milieu: Optional[str] = None, 
                              options: Dict[str, Any] = None) -> bytes:
        """
        Retrieves sector map image as raw bytes.
        Endpoint: https://travellermap.com/api/poster
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters:
                - style: Map style (e.g., 'poster', 'print')
                - scale: Scale factor (default: 64 for poster style)
                - width: Width in pixels
                - height: Height in pixels
                - options: Comma-separated list of options (e.g., 'grid,border,routes')
                
        Returns: 
            Raw image data as bytes.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        # Add any provided options
        if options:
            params.update(options)
        else:
            # Default options for good quality
            params["style"] = "poster"
            params["scale"] = 64
            
        try:
            return self._make_api_request("poster", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching sector image: {e}")
            raise
    
    def get_sector_pixmap(self, sector: str, milieu: Optional[str] = None, 
                         options: Dict[str, Any] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Retrieves sector map as a QPixmap.
        Endpoint: https://travellermap.com/api/poster
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters (see get_sector_image_bytes)
                
        Returns: 
            Tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        try:
            image_data = self.get_sector_image_bytes(sector, milieu, options)
            
            # Convert to QPixmap
            qdata = QByteArray(image_data)
            pixmap = QPixmap()
            if pixmap.loadFromData(qdata):
                return pixmap, None
            else:
                error_msg = "Failed to load image data into QPixmap"
                logger.error(error_msg)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"Error retrieving sector map: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def save_sector_image(self, sector: str, save_path: Optional[str] = None, 
                         milieu: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Downloads and saves sector map image.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            save_path: Optional path to save the image. If None, saves to default location.
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters (see get_sector_image_bytes)
            
        Returns: 
            Path where the image was saved.
        """
        image_data = self.get_sector_image_bytes(sector, milieu, options)
        
        if not save_path:
            folder = os.path.join("database", "content", "images", "sector")
            os.makedirs(folder, exist_ok=True)
            # Include milieu in filename to avoid overwriting images from different milieux
            milieu_suffix = f"_{milieu or self.milieu}" if milieu or self.milieu else ""
            save_path = os.path.join(folder, f"{sector.replace(' ', '_')}{milieu_suffix}_map.png")
        
        with open(save_path, "wb") as f:
            f.write(image_data)
        return save_path
    
    def get_system_image_bytes(self, sector: str, hex_code: str, milieu: Optional[str] = None, 
                              options: Dict[str, Any] = None) -> bytes:
        """
        Retrieves system map image as raw bytes.
        Endpoint: https://travellermap.com/api/jumpmap
        
        Args:
            sector: Sector name or T5SS abbreviation.
            hex_code: Hex code of the system (e.g. "1910")
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters:
                - jump: Jump distance (default: 1)
                - style: Map style (e.g., 'poster', 'print')
                - scale: Scale factor
                
        Returns: 
            Raw image data as bytes.
        """
        params = {
            "sector": sector,
            "hex": hex_code
        }
        if milieu:
            params["milieu"] = milieu
            
        # Add any provided options
        if options:
            params.update(options)
        else:
            # Default options
            params["jump"] = 2
            params["style"] = "poster"
            
        try:
            return self._make_api_request("jumpmap", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching system image: {e}")
            raise
    
    def get_system_pixmap(self, sector: str, hex_code: str, milieu: Optional[str] = None, 
                         options: Dict[str, Any] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Retrieves system map as a QPixmap.
        Endpoint: https://travellermap.com/api/jumpmap
        
        Args:
            sector: Sector name or T5SS abbreviation.
            hex_code: Hex code of the system (e.g. "1910")
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters (see get_system_image_bytes)
                
        Returns: 
            Tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        try:
            image_data = self.get_system_image_bytes(sector, hex_code, milieu, options)
            
            # Convert to QPixmap
            qdata = QByteArray(image_data)
            pixmap = QPixmap()
            if pixmap.loadFromData(qdata):
                return pixmap, None
            else:
                error_msg = "Failed to load image data into QPixmap"
                logger.error(error_msg)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"Error retrieving system map: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def save_system_image(self, sector: str, hex_code: str, save_path: Optional[str] = None, 
                         milieu: Optional[str] = None, options: Dict[str, Any] = None) -> str:
        """
        Downloads and saves system map image.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            hex_code: Hex code of the system (e.g. "1910")
            save_path: Optional path to save the image. If None, saves to default location.
            milieu: Optional milieu code. If None, uses the instance default.
            options: Optional dictionary with additional parameters (see get_system_image_bytes)
            
        Returns: 
            Path where the image was saved.
        """
        image_data = self.get_system_image_bytes(sector, hex_code, milieu, options)
        
        if not save_path:
            folder = os.path.join("database", "content", "images", "system")
            os.makedirs(folder, exist_ok=True)
            # Include milieu in filename to avoid overwriting images from different milieux
            milieu_suffix = f"_{milieu or self.milieu}" if milieu or self.milieu else ""
            save_path = os.path.join(
                folder, 
                f"{sector.replace(' ', '_')}_{hex_code}{milieu_suffix}_map.png"
            )
        
        with open(save_path, "wb") as f:
            f.write(image_data)
        return save_path
    
    # -----------------------------
    # Search and Other Endpoints
    # -----------------------------
    def search(self, query: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for worlds, sectors, etc.
        Endpoint: https://travellermap.com/api/search
        
        Args:
            query: Search query string
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns: 
            Search results as a dictionary with structure:
            {
                "Results": {
                    "Count": <int>,
                    "Items": [
                        {
                            "Name": <str>,
                            "Sector": <str>,
                            "Hex": <str>,
                            "Type": <str>,
                            ...
                        },
                        ...
                    ]
                }
            }
        """
        params = {"q": query}
        if milieu:
            params["milieu"] = milieu
            
        try:
            return self._make_api_request("search", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    def get_available_milieux(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all available milieux.
        Endpoint: https://travellermap.com/api/milieux
        
        Returns: 
            List of milieu objects with structure:
            [
                {
                    "Code": <str>,
                    "Name": <str>,
                    "IsDefault": <bool>
                },
                ...
            ]
        """
        try:
            return self._make_api_request("milieux", use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching milieux: {e}")
            raise
    
    def set_milieu(self, milieu: str):
        """
        Sets the default milieu for this API instance.
        
        Args:
            milieu: Milieu code (e.g., 'M1105', 'IW')
        """
        self.milieu = milieu


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create API instance
    api = TravellerMapAPI()
    
    try:
        # Get universe data
        print("Fetching universe data...")
        universe = api.get_universe()
        if "Sectors" in universe:
            print(f"Found {len(universe['Sectors'])} sectors")
        
        # Get data for Spinward Marches
        sector_name = "Spinward Marches"
        print(f"\nFetching data for {sector_name}...")
        sector_data = api.get_sector_data(sector_name)
        
        print(f"Metadata: {json.dumps(sector_data['metadata'], indent=2)[:200]}...")
        print(f"Systems: {len(sector_data['systems'])} found")
        
        # Download sector map
        print(f"\nDownloading map for {sector_name}...")
        map_path = api.save_sector_image(sector_name)
        print(f"Map saved to: {map_path}")
        
        # Search for a world
        search_term = "Regina"
        print(f"\nSearching for '{search_term}'...")
        search_results = api.search(search_term)
        if search_results.get("Results", {}).get("Count", 0) > 0:
            print(f"Found {search_results['Results']['Count']} results")
            first_result = search_results["Results"]["Items"][0]
            print(f"First result: {json.dumps(first_result, indent=2)}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"ERROR: {e}")
