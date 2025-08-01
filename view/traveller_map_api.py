import logging
import urllib.request
import urllib.parse
import os
import hashlib
import time
import socket
from typing import Optional, Dict, Any, Tuple
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice

logger = logging.getLogger(__name__)

class TravellerMapAPI:
    """Class for interacting with the Traveller Map API."""
    
    BASE_URL = "https://travellermap.com/api"
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".traveller_map_cache")
    
    # Error handling constants
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    @classmethod
    def ensure_cache_dir(cls):
        """Ensure the cache directory exists."""
        if not os.path.exists(cls.CACHE_DIR):
            try:
                os.makedirs(cls.CACHE_DIR)
                logger.info(f"Created cache directory: {cls.CACHE_DIR}")
            except Exception as e:
                logger.error(f"Failed to create cache directory: {e}")
                return False
        return True
    
    @classmethod
    def get_cache_path(cls, url):
        """Get the cache path for a URL."""
        # Create a hash of the URL to use as the filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(cls.CACHE_DIR, f"{url_hash}.png")
    
    @classmethod
    def get_sector_map(cls, sector_name: str, milieu: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Fetch a sector map from the Traveller Map API.
        
        Args:
            sector_name: Name of the sector to fetch
            milieu: Optional milieu code (e.g., 'M1105', 'IW')
            options: Optional dictionary of additional API options
            
        Returns:
            Tuple of (QPixmap containing the sector map image or None if failed, Error message or None if successful)
        """
        if not sector_name:
            return None, "No sector name provided"
            
        # Build the API URL
        url = f"{cls.BASE_URL}/poster?sector={urllib.parse.quote(sector_name)}"
        
        # Add milieu parameter if provided
        if milieu:
            url += f"&milieu={urllib.parse.quote(milieu)}"
        
        # Add any additional options
        if options:
            for key, value in options.items():
                url += f"&{key}={urllib.parse.quote(str(value))}"
        
        logger.info(f"Fetching sector map from: {url}")
        
        # Check if we have a cached version
        if cls.ensure_cache_dir():
            cache_path = cls.get_cache_path(url)
            if os.path.exists(cache_path):
                logger.info(f"Loading sector map from cache: {cache_path}")
                pixmap = QPixmap(cache_path)
                if not pixmap.isNull():
                    return pixmap, None
                else:
                    logger.warning("Cached image is invalid, fetching from API")
                    # Delete invalid cache file
                    try:
                        os.remove(cache_path)
                        logger.info(f"Deleted invalid cache file: {cache_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete invalid cache file: {e}")
        
        # Implement retry logic
        retry_count = 0
        while retry_count < cls.MAX_RETRIES:
            try:
                # Fetch the image data
                logger.info(f"Sending request to: {url} (attempt {retry_count + 1}/{cls.MAX_RETRIES})")
                response = urllib.request.urlopen(url, timeout=10)  # Add timeout
                data = response.read()
                logger.info(f"Received {len(data)} bytes of data")
                
                # Convert to QPixmap
                image = QImage()
                if image.loadFromData(data):
                    pixmap = QPixmap.fromImage(image)
                    
                    # Save to cache
                    if cls.ensure_cache_dir():
                        cache_path = cls.get_cache_path(url)
                        logger.info(f"Saving sector map to cache: {cache_path}")
                        pixmap.save(cache_path, "PNG")
                    
                    return pixmap, None
                else:
                    error_msg = "Failed to load image data"
                    logger.error(error_msg)
                    retry_count += 1
                    if retry_count < cls.MAX_RETRIES:
                        time.sleep(cls.RETRY_DELAY)
                    else:
                        return None, error_msg
                    
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP Error: {e.code} - {e.reason}"
                logger.error(error_msg)
                return None, error_msg
                
            except urllib.error.URLError as e:
                error_msg = f"URL Error: {e.reason}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except socket.timeout:
                error_msg = "Connection timed out"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except Exception as e:
                error_msg = f"Error fetching sector map: {str(e)}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
        # If we get here, all retries failed
        return None, "Failed to fetch sector map after multiple attempts"
    
    @classmethod
    def get_system_map(cls, sector_name: str, hex_code: str, milieu: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
        """
        Fetch a system map from the Traveller Map API.
        
        Args:
            sector_name: Name of the sector
            hex_code: Hex code of the system (e.g. "1910")
            milieu: Optional milieu code (e.g., 'M1105', 'IW')
            options: Optional dictionary of additional API options
            
        Returns:
            Tuple of (QPixmap containing the system map image or None if failed, Error message or None if successful)
        """
        if not sector_name or not hex_code:
            return None, "Missing sector name or hex code"
            
        # Build the API URL
        url = f"{cls.BASE_URL}/jumpmap?sector={urllib.parse.quote(sector_name)}&hex={hex_code}"
        
        # Add any additional options
        if options:
            for key, value in options.items():
                url += f"&{key}={urllib.parse.quote(str(value))}"
        
        logger.info(f"Fetching system map from: {url}")
        
        # Check if we have a cached version
        if cls.ensure_cache_dir():
            cache_path = cls.get_cache_path(url)
            if os.path.exists(cache_path):
                logger.info(f"Loading system map from cache: {cache_path}")
                pixmap = QPixmap(cache_path)
                if not pixmap.isNull():
                    return pixmap, None
                else:
                    logger.warning("Cached image is invalid, fetching from API")
                    # Delete invalid cache file
                    try:
                        os.remove(cache_path)
                        logger.info(f"Deleted invalid cache file: {cache_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete invalid cache file: {e}")
        
        # Implement retry logic
        retry_count = 0
        while retry_count < cls.MAX_RETRIES:
            try:
                # Fetch the image data
                logger.info(f"Sending request to: {url} (attempt {retry_count + 1}/{cls.MAX_RETRIES})")
                response = urllib.request.urlopen(url, timeout=10)  # Add timeout
                data = response.read()
                logger.info(f"Received {len(data)} bytes of data")
                
                # Convert to QPixmap
                image = QImage()
                if image.loadFromData(data):
                    pixmap = QPixmap.fromImage(image)
                    
                    # Save to cache
                    if cls.ensure_cache_dir():
                        cache_path = cls.get_cache_path(url)
                        logger.info(f"Saving system map to cache: {cache_path}")
                        pixmap.save(cache_path, "PNG")
                    
                    return pixmap, None
                else:
                    error_msg = "Failed to load image data"
                    logger.error(error_msg)
                    retry_count += 1
                    if retry_count < cls.MAX_RETRIES:
                        time.sleep(cls.RETRY_DELAY)
                    else:
                        return None, error_msg
                    
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP Error: {e.code} - {e.reason}"
                logger.error(error_msg)
                return None, error_msg
                
            except urllib.error.URLError as e:
                error_msg = f"URL Error: {e.reason}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except socket.timeout:
                error_msg = "Connection timed out"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except Exception as e:
                error_msg = f"Error fetching system map: {str(e)}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
        # If we get here, all retries failed
        return None, "Failed to fetch system map after multiple attempts"
    
    @classmethod
    def get_world_data(cls, sector_name: str, hex_code: str, milieu: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Fetch world data from the Traveller Map API.
        
        Args:
            sector_name: Name of the sector
            hex_code: Hex code of the system (e.g. "1910")
            milieu: Optional milieu code (e.g., 'M1105', 'IW')
            
        Returns:
            Tuple of (Dictionary containing world data or None if failed, Error message or None if successful)
            
    except Exception as e:
        error_msg = f"Error fetching sector map: {str(e)}"
        logger.error(error_msg)
        retry_count += 1
        if retry_count < cls.MAX_RETRIES:
            logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
            time.sleep(cls.RETRY_DELAY)
        else:
            return None, error_msg
            
# If we get here, all retries failed
return None, "Failed to fetch sector map after multiple attempts"

@classmethod
def get_system_map(cls, sector_name: str, hex_code: str, milieu: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[Optional[QPixmap], Optional[str]]:
    """
    Fetch a system map from the Traveller Map API.
    
    Args:
        sector_name: Name of the sector
        hex_code: Hex code of the system (e.g. "1910")
        milieu: Optional milieu code (e.g., 'M1105', 'IW')
        options: Optional dictionary of additional API options
        
    Returns:
        Tuple of (QPixmap containing the system map image or None if failed, Error message or None if successful)
    """
    if not sector_name or not hex_code:
        return None, "Missing sector name or hex code"
        
    # Build the API URL
    url = f"{cls.BASE_URL}/jumpmap?sector={urllib.parse.quote(sector_name)}&hex={hex_code}"
    
    # Add milieu parameter if provided
    if milieu:
        url += f"&milieu={urllib.parse.quote(milieu)}"
    
    # Add any additional options
    if options:
        for key, value in options.items():
            url += f"&{key}={urllib.parse.quote(str(value))}"
    
    logger.info(f"Fetching system map from: {url}")
    
    # Check if we have a cached version
    if cls.ensure_cache_dir():
        cache_path = cls.get_cache_path(url)
        if os.path.exists(cache_path):
            logger.info(f"Loading system map from cache: {cache_path}")
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                return pixmap, None
            else:
                logger.warning("Cached image is invalid, fetching from API")
                # Delete invalid cache file
                try:
                    os.remove(cache_path)
                    logger.info(f"Deleted invalid cache file: {cache_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete invalid cache file: {e}")
    
    # Implement retry logic
    retry_count = 0
    while retry_count < cls.MAX_RETRIES:
        try:
            # Fetch the image data
            logger.info(f"Sending request to: {url} (attempt {retry_count + 1}/{cls.MAX_RETRIES})")
            response = urllib.request.urlopen(url, timeout=10)  # Add timeout
            data = response.read()
            logger.info(f"Received {len(data)} bytes of data")
            
            # Convert to QPixmap
            image = QImage()
            if image.loadFromData(data):
                pixmap = QPixmap.fromImage(image)
        retry_count = 0
        while retry_count < cls.MAX_RETRIES:
            try:
                # Fetch the data
                logger.info(f"Fetching world data from: {url} (attempt {retry_count + 1}/{cls.MAX_RETRIES})")
                response = urllib.request.urlopen(url, timeout=10)  # Add timeout
                data = response.read().decode('utf-8')
                
                # Parse the JSON data
                import json
                return json.loads(data), None
                    
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP Error: {e.code} - {e.reason}"
                logger.error(error_msg)
                return None, error_msg
                
            except urllib.error.URLError as e:
                error_msg = f"URL Error: {e.reason}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except socket.timeout:
                error_msg = "Connection timed out"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON data: {str(e)}"
                logger.error(error_msg)
                return None, error_msg
                
            except Exception as e:
                error_msg = f"Error fetching world data: {str(e)}"
                logger.error(error_msg)
                retry_count += 1
                if retry_count < cls.MAX_RETRIES:
                    logger.info(f"Retrying in {cls.RETRY_DELAY} seconds...")
                    time.sleep(cls.RETRY_DELAY)
                else:
                    return None, error_msg
                    
        # If we get here, all retries failed
        return None, "Failed to fetch world data after multiple attempts"
