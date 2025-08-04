import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Tuple
import hashlib
import time
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QByteArray

logger = logging.getLogger(__name__)

# Constants for error messages
ERROR_LOADING_IMAGE = "Failed to load image data"
ERROR_API_REQUEST = "API request failed"
ERROR_PARSING_DATA = "Failed to parse data"

class TravellerMapAPI:
    """
    Traveller Map API client for accessing map data, sector information, and more.
    This implementation fixes issues with the original API client and adds robust
    error handling, caching, and consistent interfaces.
    """
    
    BASE_URL = "https://travellermap.com"
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".traveller_map_cache")
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, base_url=None, milieu="M1105"):
        """
        Initialize the Traveller Map API client.
        
        Args:
            base_url: Optional custom base URL (defaults to https://travellermap.com)
            milieu: Default milieu code to use (defaults to M1105)
        """
        self.base_url = base_url or self.BASE_URL
        self.base_url = self.base_url.rstrip('/')
        self.milieu = milieu
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
    
    def _get_cache_path(self, url, params=None):
        """
        Generate a cache file path for a URL.
        
        Args:
            url: The URL to generate a cache path for
            params: Optional query parameters
            
        Returns:
            Path to the cache file
        """
        # Create a unique hash based on URL and params
        if params:
            cache_key = f"{url}?{json.dumps(params, sort_keys=True)}"
        else:
            cache_key = url
            
        url_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Use appropriate extension based on URL path
        if '/image' in url or '/poster' in url or '/jumpmap' in url or '/tile' in url:
            extension = '.png'
        else:
            extension = '.json'
            
        return os.path.join(self.CACHE_DIR, f"{url_hash}{extension}")
    
    def _make_api_request(self, endpoint, params=None, use_api_prefix=True, use_cache=True):
        """
        Make a request to the Traveller Map API with proper error handling.
        
        Args:
            endpoint: API endpoint path (without leading slash)
            params: Dictionary of query parameters
            use_api_prefix: Whether to use /api/ prefix (True) or /data/ prefix (False)
            use_cache: Whether to use cache for this request
            
        Returns:
            Response data (JSON or text depending on endpoint)
            
        Raises:
            requests.HTTPError: If the API returns an error status code
            requests.RequestException: For other request failures
            ValueError: For parsing errors
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
        logger.info(f"API request: {url} with params {params}")
        
        # Check cache first if enabled
        if use_cache:
            cache_path = self._get_cache_path(url, params)
            if os.path.exists(cache_path):
                logger.info(f"Loading from cache: {cache_path}")
                try:
                    with open(cache_path, 'rb') as f:
                        content = f.read()
                        if content:
                            # For JSON data, we need to decode it
                            if cache_path.endswith('.json'):
                                try:
                                    return json.loads(content.decode('utf-8'))
                                except json.JSONDecodeError:
                                    # Invalid cache, remove it
                                    os.remove(cache_path)
                                    logger.warning(f"Removed invalid JSON cache: {cache_path}")
                            else:
                                return content
                except Exception as e:
                    logger.warning(f"Failed to read cache: {e}")
        
        # Make the request with retry logic
        retry_count = 0
        last_error = None
        
        while retry_count < self.MAX_RETRIES:
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                # Cache the response if caching is enabled
                if use_cache and self._ensure_cache_dir():
                    cache_path = self._get_cache_path(url, params)
                    with open(cache_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Cached response to: {cache_path}")
                
                # Return appropriate type based on content
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.json()
                elif '/image' in url or '/poster' in url or '/jumpmap' in url or '/tile' in url:
                    return response.content
                else:
                    return response.text
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"Request failed (attempt {retry_count+1}/{self.MAX_RETRIES}): {e}")
                retry_count += 1
                if retry_count < self.MAX_RETRIES:
                    logger.info(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
        
        # If we get here, all retries failed
        logger.error(f"Failed after {self.MAX_RETRIES} attempts: {last_error}")
        raise last_error or ValueError(ERROR_API_REQUEST)
    
    # -----------------------------
    # Universe Endpoints
    # -----------------------------
    def get_universe(self, milieu: Optional[str] = None):
        """
        Retrieves the universe data.
        Endpoint: https://travellermap.com/data
        
        Args:
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: A JSON object with a "Sectors" key.
        """
        params = {}
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("", params, use_api_prefix=False)
    
    # -----------------------------
    # Sector Endpoints
    # -----------------------------
    def get_sector_sec(self, sector, milieu: Optional[str] = None):
        """
        Retrieves sector data in legacy SEC format.
        Endpoint: https://travellermap.com/data/sector/sec
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: Text data.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("sector/sec", params, use_api_prefix=False)
    
    def parse_sec_line(self, line):
        """
        Parses a single line of SEC data.
        Expected format: HEX NAME UPP [other tokens...]
        
        Args:
            line: A line of SEC data
            
        Returns: Dictionary with keys: 'hex', 'name', 'upp', and optionally 'raw_data'
        """
        tokens = line.split()
        if len(tokens) < 3:
            return None
        data = {"hex": tokens[0], "name": tokens[1], "upp": tokens[2]}
        if len(tokens) > 3:
            data["raw_data"] = " ".join(tokens[3:])
        return data
    
    def get_sector_t5(self, sector, milieu: Optional[str] = None):
        """
        Retrieves sector data in T5 format.
        Endpoint: https://travellermap.com/data/sector
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: Text data in T5 format.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("sector", params, use_api_prefix=False)
    
    def get_sectors(self, milieu: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the list of all sectors with their metadata.
        
        Args:
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns:
            List of sector dictionaries with keys like 'Name', 'X', 'Y', 'Milieu', etc.
        """
        universe_data = self.get_universe(milieu)
        if not isinstance(universe_data, dict) or "Sectors" not in universe_data:
            raise ValueError("Universe data does not contain 'Sectors'")
        return universe_data["Sectors"]
    
    def get_sector_metadata(self, sector: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves metadata for a sector.
        Endpoint: https://travellermap.com/api/metadata
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns:
            Dictionary containing sector metadata.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("metadata", params, use_api_prefix=True)
    
    def get_sector_data(self, sector: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves detailed sector data including metadata and system information.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code.
            
        Returns:
            Dictionary containing sector data, including 'metadata' and 'systems' keys.
        """
        try:
            # Get metadata
            metadata = self.get_sector_metadata(sector, milieu)
            
            # Get system data
            t5_data = self.get_sector_t5(sector, milieu)
            systems = self._parse_t5_systems(t5_data)
            
            return {
                "metadata": metadata,
                "systems": systems
            }
            
        except Exception as e:
            logger.error(f"Error getting sector data: {e}")
            raise
    
    def _parse_system_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single system line from T5 data.
        
        Args:
            line: A line from T5 format data
            
        Returns:
            Dictionary containing parsed system data
        """
        parts = line.split()
        if len(parts) < 2:
            return {}
            
        system = {
            "hex": parts[0],
            "name": parts[1]
        }
        
        # Add UWP if available (position 2)
        if len(parts) > 2:
            system["uwp"] = parts[2]
            
        # Parse trade codes (position 3+)
        trade_codes = []
        extensions = []
        
        in_extensions = False
        for i in range(3, len(parts)):
            if parts[i] in ["{", "("]:
                in_extensions = True
                extensions.append(parts[i])
            elif in_extensions:
                extensions.append(parts[i])
            else:
                trade_codes.append(parts[i])
                
        if trade_codes:
            system["trade_codes"] = " ".join(trade_codes)
            
        if extensions:
            system["extensions"] = extensions
            
        return system
    
    def _parse_t5_systems(self, t5_data: str) -> List[Dict[str, Any]]:
        """
        Parses T5 data into a list of system dictionaries.
        
        Args:
            t5_data: Raw T5 format data.
            
        Returns:
            List of system dictionaries with parsed data.
        """
        systems = []
        
        for line in t5_data.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('@'):
                continue
                
            if self._is_system_line(line):
                system = self._parse_system_line(line)
                if system:
                    systems.append(system)
                    
        return systems
    
    def _is_system_line(self, line: str) -> bool:
        """
        Check if a line represents a system (starts with hex code).
        
        Args:
            line: A line from T5 format data
            
        Returns:
            True if the line represents a system, False otherwise
        """
        import re
        # Match lines that start with a hex code (e.g., "0101")
        return bool(re.match(r'^[0-9A-Fa-f]{4}', line))
    
    # -----------------------------
    # Image Endpoints
    # -----------------------------
    def download_sector_image(self, sector, save_path=None, milieu: Optional[str] = None, options: Dict[str, Any] = None):
        """
        Downloads sector map image.
        Endpoint: https://travellermap.com/api/poster
        
        Args:
            sector: Sector name or T5SS abbreviation.
            save_path: Optional path to save the image. If None, saves to default location.
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            options: Optional dictionary of additional parameters
            
        Returns: Path where the image was saved.
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
            
        # Add any provided options
        if options:
            params.update(options)
            
        # Use the poster API for better quality images
        image_data = self._make_api_request("poster", params, use_api_prefix=True)
        
        if not save_path:
            folder = os.path.join("database", "content", "images", "sector")
            os.makedirs(folder, exist_ok=True)
            # Include milieu in filename to avoid overwriting images from different milieux
            milieu_suffix = f"_{milieu or self.milieu}" if milieu or self.milieu else ""
            save_path = os.path.join(folder, f"{sector.replace(' ', '_')}{milieu_suffix}_map.png")
        
        with open(save_path, "wb") as f:
            f.write(image_data)
        return save_path
    
    def get_sector_map(self, sector_name, milieu: Optional[str] = None, options: Dict[str, Any] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Retrieves a sector map using the poster API endpoint.
        Endpoint: https://travellermap.com/api/poster
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code
            options: Optional dictionary with additional parameters:
                - style: Map style (e.g., 'poster', 'print')
                - scale: Scale factor (default: 64 for poster style)
                - width: Width in pixels
                - height: Height in pixels
                - options: Comma-separated list of options (e.g., 'grid,border,routes')
                
        Returns: A tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        params = {"sector": sector_name}
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
            image_data = self._make_api_request("poster", params, use_api_prefix=True)
            
            # Convert to QPixmap
            qdata = QByteArray(image_data)
            pixmap = QPixmap()
            if pixmap.loadFromData(qdata):
                return pixmap, None
            else:
                logger.error(ERROR_LOADING_IMAGE)
                return None, ERROR_LOADING_IMAGE
                
        except Exception as e:
            error_msg = f"Error retrieving sector map: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_system_map(self, sector_name: str, hex_code: str, milieu: Optional[str] = None, options: Dict[str, Any] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Retrieves a system map using the jumpmap API endpoint.
        Endpoint: https://travellermap.com/api/jumpmap
        
        Args:
            sector_name: Name or abbreviation of the sector
            hex_code: Hex code of the system (e.g. "1910")
            milieu: Optional milieu code
            options: Optional dictionary with additional parameters:
                - jump: Jump distance (default: 1)
                - style: Map style (e.g., 'poster', 'print')
                - scale: Scale factor
                
        Returns: A tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        params = {
            "sector": sector_name,
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
            image_data = self._make_api_request("jumpmap", params, use_api_prefix=True)
            
            # Convert to QPixmap
            qdata = QByteArray(image_data)
            pixmap = QPixmap()
            if pixmap.loadFromData(qdata):
                return pixmap, None
            else:
                logger.error(ERROR_LOADING_IMAGE)
                return None, ERROR_LOADING_IMAGE
                
        except Exception as e:
            error_msg = f"Error retrieving system map: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    # -----------------------------
    # Search and Other Endpoints
    # -----------------------------
    def get_available_milieux(self):
        """
        Retrieves a list of all available milieux.
        Endpoint: https://travellermap.com/api/milieux
        
        Returns: List of milieu objects with 'Code' and 'IsDefault' properties.
        """
        return self._make_api_request("milieux", use_api_prefix=True)
    
    def set_milieu(self, milieu: str):
        """
        Sets the default milieu for this API instance.
        
        Args:
            milieu: Milieu code (e.g., 'M1105', 'IW')
        """
        self.milieu = milieu
        
    def search(self, query: str, milieu: Optional[str] = None):
        """
        Search for worlds, sectors, etc.
        Endpoint: https://travellermap.com/api/search
        
        Args:
            query: Search query string
            milieu: Optional milieu code
            
        Returns: Search results as a dictionary
        """
        params = {"q": query}
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("search", params, use_api_prefix=True)
    
    def get_world_data(self, sector_name: str, hex_code: str, milieu: Optional[str] = None):
        """
        Get detailed data for a specific world.
        Endpoint: https://travellermap.com/api/sec
        
        Args:
            sector_name: Name or abbreviation of the sector
            hex_code: Hex code of the world (e.g. "1910")
            milieu: Optional milieu code
            
        Returns: World data as a dictionary
        """
        params = {
            "sector": sector_name,
            "hex": hex_code
        }
        if milieu:
            params["milieu"] = milieu
            
        return self._make_api_request("sec", params, use_api_prefix=True)


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
        print(f"Found {len(universe['Sectors'])} sectors")
        
        # Get data for Spinward Marches
        sector_name = "Spinward Marches"
        print(f"\nFetching data for {sector_name}...")
        sector_data = api.get_sector_data(sector_name)
        
        print(f"Metadata: {json.dumps(sector_data['metadata'], indent=2)[:200]}...")
        print(f"Systems: {len(sector_data['systems'])} found")
        
        # Download sector map
        print(f"\nDownloading map for {sector_name}...")
        map_path = api.download_sector_image(sector_name)
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
