#!/usr/bin/env python3
"""
Traveller Map API Client - Fixed Implementation V2

This module provides a robust client for interacting with the Traveller Map API.
It includes support for:
- Fetching universe data
- Fetching sector data (metadata, T5, SEC)
- Fetching sector and system images
- Searching for worlds
- Getting available milieux
- Caching responses
- Retry logic with exponential backoff

Example usage:
    api = TravellerMapAPI()
    
    # Get sector data
    sector_data = api.get_sector_data("Spinward Marches")
    
    # Get sector image
    pixmap, error = api.get_sector_pixmap("Spinward Marches")
    
    # Search for worlds
    results = api.search("Regina")
"""

import os
import re
import time
import json
import pickle
import hashlib
import logging
import requests
from typing import Dict, List, Tuple, Any, Optional, Union

# For image handling
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QByteArray

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TravellerMapAPI:
    """Client for interacting with the Traveller Map API."""
    
    # Constants
    BASE_URL = "https://travellermap.com"
    API_PREFIX = "/api"
    DATA_PREFIX = "/data"
    CACHE_DIR = "database/cache"
    IMAGES_DIR = "database/content/images"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self, api_base_url="https://travellermap.com", milieu="M1105", timeout=10):
        """
        Initialize the Traveller Map API client.
        
        Args:
            api_base_url: Base URL for the Traveller Map API
            milieu: Default milieu to use
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url
        self.milieu = milieu
        self.request_timeout = timeout  # Use a different name to avoid confusion with TIMEOUT constant
        self.TIMEOUT = timeout  # For backward compatibility
        self.cache_dir = os.path.join("database", "cache")
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
            
        # Ensure cache directory exists
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        logger.info(f"Created cache directory: {self.CACHE_DIR}")
        
        # Also ensure images directory exists
        os.makedirs(os.path.join(self.IMAGES_DIR, "sector"), exist_ok=True)
        os.makedirs(os.path.join(self.IMAGES_DIR, "system"), exist_ok=True)
        return True
    
    def _get_cache_path(self, endpoint, params=None, use_api_prefix=True):
        """
        Get the cache path for a request.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            use_api_prefix: Whether to use the API prefix
            
        Returns:
            Path to the cache file
        """
        # Build the URL
        prefix = self.API_PREFIX if use_api_prefix else self.DATA_PREFIX
        url = f"{self.api_base_url}{prefix}/{endpoint}"
        
        # Add parameters to the cache key
        if params:
            param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key = f"{url}?{param_str}"
        else:
            cache_key = url
            
        # Create a hash of the cache key
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return os.path.join(self.CACHE_DIR, f"{cache_hash}.cache")
    
    def _make_request(self, url, params=None):
        """
        Make a request with retry logic.
        
        Args:
            url: URL to request
            params: Request parameters
            
        Returns:
            Response object or None on failure
        """
        retries = 0
        while retries <= self.MAX_RETRIES:
            try:
                logger.debug(f"Requesting: {url}")
                response = requests.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries <= self.MAX_RETRIES:
                    # Exponential backoff
                    wait_time = self.RETRY_DELAY * (2 ** (retries - 1))
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time:.1f}s ({retries}/{self.MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.MAX_RETRIES} retries: {e}")
                    return None
    
    def _process_response(self, response, endpoint):
        """
        Process the API response.
        
        Args:
            response: Response object
            endpoint: API endpoint
            
        Returns:
            Processed response data
        """
        if not response:
            return None
            
        content_type = response.headers.get('content-type', '')
        
        # Determine the response type
        if content_type.startswith('application/json'):
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response from {endpoint}")
                return None
        elif content_type.startswith('image/') or endpoint in ['poster', 'jumpmap', 'tile'] or '/image' in endpoint:
            return response.content
        else:
            return response.text
    
    def _api_request(self, endpoint, params=None, use_api_prefix=True, use_cache=True):
        """
        Make a request to the Traveller Map API.
        
        Args:
            endpoint: API endpoint to call
            params: Optional parameters
            use_api_prefix: Whether to use the API prefix or data prefix
            use_cache: Whether to use cache
            
        Returns:
            Response data (JSON, text, or binary)
        """
        # Build the URL
        prefix = self.API_PREFIX if use_api_prefix else self.DATA_PREFIX
        url = f"{self.api_base_url}{prefix}/{endpoint}"
        
        # Check cache if enabled
        if use_cache:
            cache_path = self._get_cache_path(endpoint, params, use_api_prefix)
            if os.path.exists(cache_path):
                logger.debug(f"Using cached response for: {url}")
                try:
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read cache: {e}")
                    # Continue with the request
        
        # Make the request
        response = self._make_request(url, params)
        data = self._process_response(response, endpoint)
        
        # Cache the response if enabled
        if use_cache and data is not None:
            cache_path = self._get_cache_path(endpoint, params, use_api_prefix)
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                logger.debug(f"Cached response to: {cache_path}")
            except Exception as e:
                logger.warning(f"Failed to write cache: {e}")
        
        return data
    
    # -----------------------------
    # Universe Endpoints
    # -----------------------------
    
    def get_universe(self):
        """
        Get universe data.
        
        Returns:
            Dictionary containing universe data
        """
        try:
            # The universe endpoint is at /api/universe
            return self._api_request("universe", use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching universe data: {e}")
            return {}
    
    # -----------------------------
    # Sector Endpoints
    # -----------------------------
    
    def get_sector_metadata(self, sector, milieu=None):
        """
        Get metadata for a sector.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            
        Returns:
            Dictionary containing sector metadata
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        try:
            return self._api_request("metadata", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error fetching sector metadata: {e}")
            return {}
    
    def get_sector_t5(self, sector, milieu=None):
        """
        Get T5 format data for a sector.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            
        Returns:
            T5 format data as a string
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        try:
            return self._api_request("sector", params, use_api_prefix=False)
        except Exception as e:
            logger.error(f"Error fetching T5 data: {e}")
            return ""
    
    def get_sector_sec(self, sector, milieu=None):
        """
        Get SEC format data for a sector.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            
        Returns:
            SEC format data as a string
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        try:
            return self._api_request("sector/sec", params, use_api_prefix=False)
        except Exception as e:
            logger.error(f"Error fetching SEC data: {e}")
            return ""
    
    def _parse_t5_data(self, t5_data):
        """
        Parse T5 format data into a list of system dictionaries.
        
        Args:
            t5_data: T5 format data as a string or bytes
            
        Returns:
            List of system dictionaries
        """
        systems = []
        
        # Handle empty data
        if not t5_data:
            return systems
        
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
    
    def get_sector_data(self, sector, milieu=None):
        """
        Get complete sector data including metadata and systems.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            
        Returns:
            Dictionary containing sector metadata and systems
        """
        try:
            # Get sector metadata
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
            return {"metadata": {}, "systems": []}
    
    # -----------------------------
    # Image Endpoints
    # -----------------------------
    
    def get_sector_image(self, sector, milieu=None, options=None):
        """
        Get a sector map image.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Binary image data or None on error
        """
        params = {"sector": sector}
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        # Add rendering options if not provided
        if not options:
            options = {"scale": "64"}  # Don't specify type, let server decide
        params.update(options)
            
        try:
            # The correct endpoint is /api/poster
            url = f"{self.api_base_url}/api/poster"
            
            # Set headers to ensure we get an image back
            headers = {"Accept": "image/png"}
            
            response = requests.get(url, params=params, headers=headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            # Check content type to ensure we got an image
            content_type = response.headers.get('content-type', '')
            logger.debug(f"Received content type: {content_type}")
            
            if not content_type.startswith('image/'):
                logger.error(f"Expected image content, got {content_type}")
                return None
                
            return response.content
        except Exception as e:
            logger.error(f"Error fetching sector image: {e}")
            return None
    
    def get_system_image(self, sector, hex_code, milieu=None, options=None):
        """
        Get a system map image.
        
        Args:
            sector: Sector name or coordinates
            hex_code: Hex code of the system
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Binary image data or None on error
        """
        params = {"sector": sector, "hex": hex_code, "jump": "6"}  # Default jump distance
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        # Add rendering options if not provided
        if not options:
            options = {"scale": "64"}  # Don't specify type, let server decide
        params.update(options)
            
        try:
            # The correct endpoint is /api/jumpmap
            url = f"{self.api_base_url}/api/jumpmap"
            
            # Set headers to ensure we get an image back
            headers = {"Accept": "image/png"}
            
            response = requests.get(url, params=params, headers=headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            # Check content type to ensure we got an image
            content_type = response.headers.get('content-type', '')
            logger.debug(f"Received content type: {content_type}")
            
            if not content_type.startswith('image/'):
                logger.error(f"Expected image content, got {content_type}")
                return None
                
            return response.content
        except Exception as e:
            logger.error(f"Error fetching system image: {e}")
            return None
    
    def get_sector_pixmap(self, sector, milieu=None, options=None):
        """
        Get a sector map as a QPixmap.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Tuple of (QPixmap, error_message)
        """
        try:
            # Add options for image format if not specified
            if not options:
                options = {"type": "png", "scale": "64"}
            elif "type" not in options:
                options["type"] = "png"
                
            image_data = self.get_sector_image(sector, milieu, options)
            if not image_data:
                return None, "Failed to retrieve sector map"
            
            # Debug the image data
            logger.debug(f"Received image data of size: {len(image_data)} bytes")
                
            # Create pixmap from image data
            pixmap = QPixmap()
            result = pixmap.loadFromData(image_data)
            
            if not result or pixmap.isNull():
                return None, "Failed to create pixmap from image data"
                
            return pixmap, None
        except Exception as e:
            logger.error(f"Error retrieving sector map: {e}")
            return None, str(e)
    
    def get_system_pixmap(self, sector, hex_code, milieu=None, options=None):
        """
        Get a system map as a QPixmap.
        
        Args:
            sector: Sector name or coordinates
            hex_code: Hex code of the system
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Tuple of (QPixmap, error_message)
        """
        try:
            # Add options for image format if not specified
            if not options:
                options = {"type": "png", "scale": "64"}
            elif "type" not in options:
                options["type"] = "png"
                
            image_data = self.get_system_image(sector, hex_code, milieu, options)
            if not image_data:
                return None, "Failed to retrieve system map"
            
            # Debug the image data
            logger.debug(f"Received image data of size: {len(image_data)} bytes")
                
            # Create pixmap from image data
            pixmap = QPixmap()
            result = pixmap.loadFromData(image_data)
            
            if not result or pixmap.isNull():
                return None, "Failed to create pixmap from image data"
                
            return pixmap, None
        except Exception as e:
            logger.error(f"Error retrieving system map: {e}")
            return None, str(e)
    
    def save_sector_image(self, sector, milieu=None, options=None):
        """
        Save a sector map image to disk.
        
        Args:
            sector: Sector name or coordinates
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Path to the saved image or None on error
        """
        try:
            image_data = self.get_sector_image(sector, milieu, options)
            if not image_data:
                return None
                
            # Create a safe filename
            safe_sector = sector.replace(" ", "_")
            milieu_str = milieu or self.milieu
            filename = f"{safe_sector}_{milieu_str}_map.png"
            filepath = os.path.join(self.IMAGES_DIR, "sector", filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            return filepath
        except Exception as e:
            logger.error(f"Error saving sector image: {e}")
            return None
    
    def save_system_image(self, sector, hex_code, milieu=None, options=None):
        """
        Save a system map image to disk.
        
        Args:
            sector: Sector name or coordinates
            hex_code: Hex code of the system
            milieu: Optional milieu code
            options: Optional rendering options
            
        Returns:
            Path to the saved image or None on error
        """
        try:
            image_data = self.get_system_image(sector, hex_code, milieu, options)
            if not image_data:
                return None
                
            # Create a safe filename
            safe_sector = sector.replace(" ", "_")
            milieu_str = milieu or self.milieu
            filename = f"{safe_sector}_{hex_code}_{milieu_str}_map.png"
            filepath = os.path.join(self.IMAGES_DIR, "system", filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            return filepath
        except Exception as e:
            logger.error(f"Error saving system image: {e}")
            return None
    
    # -----------------------------
    # Search Endpoints
    # -----------------------------
    
    def search(self, query, milieu=None):
        """
        Search for worlds.
        
        Args:
            query: Search query
            milieu: Optional milieu code
            
        Returns:
            Dictionary containing search results
        """
        params = {"q": query}
        if milieu:
            params["milieu"] = milieu
        else:
            params["milieu"] = self.milieu
            
        try:
            return self._api_request("search", params, use_api_prefix=True)
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {"Results": {"Count": 0, "Items": []}}
    
    # -----------------------------
    # Milieu Endpoints
    # -----------------------------
    
    def get_available_milieux(self):
        """
        Get available milieux.
        
        Returns:
            List of milieu dictionaries
        """
        try:
            data = self._api_request("milieux", use_api_prefix=True)
            if data and isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Error fetching milieux: {e}")
            return []


# Example usage
if __name__ == "__main__":
    api = TravellerMapAPI()
    
    # Get sector data
    sector_data = api.get_sector_data("Spinward Marches")
    print(f"Found {len(sector_data['systems'])} systems in Spinward Marches")
    
    # Get sector image
    pixmap, error = api.get_sector_pixmap("Spinward Marches")
    if pixmap and not error:
        print(f"Sector image size: {pixmap.width()}x{pixmap.height()}")
    else:
        print(f"Error: {error}")
    
    # Search for worlds
    results = api.search("Regina")
    if "Results" in results and results["Results"]["Count"] > 0:
        print(f"Found {results['Results']['Count']} results for 'Regina'")
        for item in results["Results"]["Items"]:
            print(f"- {item.get('Name', 'Unknown')} in {item.get('Sector', 'Unknown')} ({item.get('Hex', 'Unknown')})")
