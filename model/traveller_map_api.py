import os
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Tuple

from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)

# Constants for error messages
ERROR_LOADING_IMAGE = "Failed to load image data"

class TravellerMapAPI:
    def __init__(self, base_url="https://travellermap.com", milieu="M1105"):
        # Base URL should not include the trailing /data; we'll add it as needed.
        self.base_url = base_url.rstrip('/')
        self.milieu = milieu

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
        url = f"{self.base_url}/data"
        params = {}
        
        # Use provided milieu or instance default
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error fetching universe data: HTTP {response.status_code}")
            
        return response.json()

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
        url = f"{self.base_url}/data/sector/sec"
        params = {"sector": sector}
        
        # Use provided milieu or instance default
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error fetching SEC sector data for '{sector}': HTTP {response.status_code}")
        return response.text

    def parse_sec_line(self, line):
        """
        Parses a single line of SEC data.
        Expected format: HEX NAME UPP [other tokens...]
        Returns a dictionary with keys: 'hex', 'name', 'upp', and optionally 'raw_data'
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
        Endpoint: https://travellermart.com/data/sector
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: Text data in T5 format.
        """
        url = f"{self.base_url}/data/sector"
        params = {"sector": sector}
        
        # Use provided milieu or instance default
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error fetching T5 sector data for '{sector}': HTTP {response.status_code}")
        return response.text
        
    def get_sectors(self, milieu: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the list of all sectors with their metadata.
        
        Args:
            milieu: Optional milieu code. If None, uses the instance default.
            
        Returns:
            List of sector dictionaries with keys like 'Name', 'X', 'Y', 'Milieu', etc.
        """
        url = f"{self.base_url}/api/universe"
        params = {}
        
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error fetching sector list: HTTP {response.status_code}")
            
        return response.json().get('Sectors', [])
        
    def get_sector_map(self, sector: str, milieu: Optional[str] = None, 
                      style: str = "poster", size: str = "1024") -> Tuple[QPixmap, str]:
        """
        Retrieves a sector map image.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code.
            style: Map style (e.g., 'poster', 'print').
            size: Image size (e.g., '512', '1024').
            
        Returns:
            Tuple of (QPixmap, error_message). If successful, error_message is empty.
        """
        try:
            url = f"{self.base_url}/api/poster"
            params = {
                "sector": sector,
                "style": style,
                "size": size,
                "accept": "image/png"
            }
            
            if milieu or self.milieu:
                params["milieu"] = milieu or self.milieu
                
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return None, f"Error {response.status_code}: {response.text}"
                
            # Create QPixmap from response content
            pixmap = QPixmap()
            if not pixmap.loadFromData(response.content):
                return None, ERROR_LOADING_IMAGE
                
            return pixmap, ""
            
        except Exception as e:
            return None, f"Error loading sector map: {str(e)}"
    
    def get_sector_data(self, sector: str, milieu: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves detailed sector data including metadata and system information.
        
        Args:
            sector: Sector name or T5SS abbreviation.
            milieu: Optional milieu code.
            
        Returns:
            Dictionary containing sector data, including 'metadata' and 'systems' keys.
            Each system in the 'systems' list includes planet data.
        """
        try:
            # Get metadata
            url = f"{self.base_url}/api/metadata"
            params = {"sector": sector}
            
            if milieu or self.milieu:
                params["milieu"] = milieu or self.milieu
                
            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise requests.HTTPError(f"Error fetching sector metadata: HTTP {response.status_code}")
                
            data = response.json()
            
            # Get system data
            t5_data = self.get_sector_t5(sector, milieu)
            if not t5_data or not t5_data.strip():
                logger.warning(f"No T5 data returned for sector {sector}")
                data['systems'] = []
                return data
                
            # Parse the T5 data to extract systems and planets
            systems = self._parse_t5_systems(t5_data)
            
            # Log the number of systems found
            logger.info(f"Found {len(systems)} systems in sector {sector}")
            
            # Add systems to the data
            data['systems'] = systems
            
            # Fetch additional planet data for each system if available
            for system in systems:
                if 'hex' in system:
                    try:
                        # Try to get additional planet data if available
                        hex_code = system['hex']
                        logger.debug(f"Fetching planet data for system {system.get('name', 'Unknown')} at hex {hex_code}")
                        
                        # Ensure planets list exists
                        if 'planets' not in system:
                            system['planets'] = []
                            
                        # If we have UWP data for the main world, make sure it's in the planets list
                        if 'UWP' in system and not any(p.get('is_main_world', False) for p in system['planets']):
                            main_world = {
                                'name': f"{system.get('name', 'Unknown')} I",
                                'UWP': system['UWP'],
                                'is_main_world': True
                            }
                            system['planets'].append(main_world)
                            
                    except Exception as planet_error:
                        logger.warning(f"Error fetching planet data for system at hex {system.get('hex', 'Unknown')}: {planet_error}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting sector data: {e}")
            raise
    
    def _parse_system_line(self, line: str) -> Dict[str, Any]:
        """Parse a single system line from T5 data."""
        parts = line.split()
        return {
            'hex': parts[0],
            'name': parts[1],
            'uwp': parts[2] if len(parts) > 2 else '',
            'trade_codes': parts[3] if len(parts) > 3 else '',
            'extensions': parts[4:] if len(parts) > 4 else []
        }
        
    def _parse_t5_systems(self, t5_data: str) -> List[Dict[str, Any]]:
        """
        Parses T5 data into a list of system dictionaries.
        
        Args:
            t5_data: Raw T5 format data.
            
        Returns:
            List of system dictionaries with parsed data.
        """
        systems = []
        current_system = None
        
        for line in t5_data.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Check if this is a system line (starts with hex code)
            if self._is_system_line(line):
                # Save the previous system if it's valid
                if current_system:
                    # Only include systems with valid data (name and UWP)
                    if (current_system.get('name') and current_system.get('name') != '?' and 
                        current_system.get('uwp') and '?' not in current_system.get('uwp', '???????')):
                        systems.append(current_system)
                
                # Parse the new system line
                current_system = self._parse_system_line(line)
                
                # Skip systems with no valid data
                if (not current_system.get('name') or current_system.get('name') == '?' or 
                    not current_system.get('uwp') or '?' in current_system.get('uwp', '???????')):
                    current_system = None
                    continue
                    
                # Initialize planets list
                if 'planets' not in current_system:
                    current_system['planets'] = []
                    
                # Add main world as first planet if UWP is available
                if 'uwp' in current_system and current_system['uwp'] and '?' not in current_system['uwp']:
                    main_world = {
                        'name': f"{current_system.get('name', 'Unknown')} I",
                        'UWP': current_system['uwp'],
                        'is_main_world': True,
                        'trade_codes': current_system.get('trade_codes', '')
                    }
                    current_system['planets'].append(main_world)
                    
            elif current_system and (line.startswith('  ') or line.startswith('\t')):  # Planet data
                # Parse planet line
                planet_data = self._parse_planet_line(line, current_system)
                if planet_data:
                    if 'planets' not in current_system:
                        current_system['planets'] = []
                    current_system['planets'].append(planet_data)
            
        # Add the last system if it's valid
        if current_system:
            if (current_system.get('name') and current_system.get('name') != '?' and 
                current_system.get('uwp') and '?' not in current_system.get('uwp', '???????')):
                systems.append(current_system)
        
        # Filter out systems with placeholder data
        filtered_systems = []
        for system in systems:
            if (system.get('name') and system.get('name') != '?' and 
                system.get('uwp') and '?' not in system.get('uwp', '???????')):
                filtered_systems.append(system)
        
        return filtered_systems
        
    def _parse_planet_line(self, line: str, system: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a planet line from T5 data.
        
        Args:
            line: Raw planet line data.
            system: The parent system dictionary.
            
        Returns:
            Dictionary with parsed planet data.
        """
        try:
            line = line.strip()
            
            # Try to extract planet name and details
            parts = line.split(':', 1)
            if len(parts) < 2:
                # Can't parse this line properly
                return None
                
            planet_name = parts[0].strip()
            planet_details = parts[1].strip()
            
            # Create base planet object
            planet = {
                'name': planet_name,
                'is_main_world': False,
                'system_name': system.get('name', 'Unknown'),
                'system_hex': system.get('hex', '????')
            }
            
            # Try to extract UWP
            import re
            uwp_match = re.search(r'([A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?)', planet_details)
            if uwp_match:
                planet['UWP'] = uwp_match.group(1)
            else:
                planet['UWP'] = '???????'
            
            # Try to extract trade codes
            trade_match = re.search(r'\(([A-Za-z0-9\s,]+)\)', planet_details)
            if trade_match:
                planet['trade_codes'] = trade_match.group(1)
            
            # Try to extract bases
            bases = []
            if ' N ' in planet_details or planet_details.endswith(' N'):
                bases.append('N')
            if ' S ' in planet_details or planet_details.endswith(' S'):
                bases.append('S')
            if ' X ' in planet_details or planet_details.endswith(' X'):
                bases.append('X')
            if ' W ' in planet_details or planet_details.endswith(' W'):
                bases.append('W')
                
            if bases:
                planet['bases'] = ''.join(bases)
                
            return planet
        except Exception as e:
            logger.warning(f"Error parsing planet line: {line} - {e}")
            return None
            
    def _is_system_line(self, line: str) -> bool:
        """Check if a line represents a system (starts with hex code)."""
        return (len(line) >= 4 and 
                line[0] in '0123456789ABCDEF' and 
                line[1] in '0123456789ABCDEF' and 
                line[2] in '0123456789ABCDEF' and 
                line[3] in '0123456789ABCDEF')

    def download_sector_image(self, sector, save_path=None, milieu: Optional[str] = None):
        """
        Downloads sector map image.
        Endpoint: https://travellermap.com/data/sector/image
        
        Args:
            sector: Sector name or T5SS abbreviation.
            save_path: Optional path to save the image. If None, saves to default location.
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            
        Returns: Path where the image was saved.
        """
        url = f"{self.base_url}/data/sector/image"
        params = {"sector": sector}
        
        # Use provided milieu or instance default
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
            
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error downloading sector image for '{sector}': HTTP {response.status_code}")
        
        if not save_path:
            folder = os.path.join("database", "content", "images", "sector")
            os.makedirs(folder, exist_ok=True)
            # Include milieu in filename to avoid overwriting images from different milieux
            milieu_suffix = f"_{milieu or self.milieu}" if milieu or self.milieu else ""
            save_path = os.path.join(folder, f"{sector.replace(' ', '_')}{milieu_suffix}_map.png")
        
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path

    def get_available_milieux(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all available milieux.
        Endpoint: https://travellermap.com/api/milieux
        
        Returns: List of milieu objects with 'Code' and 'IsDefault' properties.
        """
        url = f"{self.base_url}/api/milieux"
        response = requests.get(url)
        if response.status_code != 200:
            raise requests.HTTPError(f"Error fetching milieux: HTTP {response.status_code}")
        return response.json()
        
    def set_milieu(self, milieu: str):
        """
        Sets the default milieu for this API instance.
        
        Args:
            milieu: Milieu code (e.g., 'M1105', 'IW')
        """
        self.milieu = milieu
        
    def get_sector_map(self, sector_name, milieu: Optional[str] = None, options: Dict[str, Any] = None):
        """
        Retrieves a sector map using the data API endpoint.
        Endpoint: https://travellermap.com/data/{sector}/image
        
        Args:
            sector_name: Name or abbreviation of the sector
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            options: Optional dictionary of rendering options:
                - style: Map style (e.g., 'poster', 'print', 'atlas')
                - scale: Scale factor (default: 64 for poster style)
                - width: Width in pixels
                - height: Height in pixels
                - options: Comma-separated list of options (e.g., 'grid,border,routes')
                
        Returns: A tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        from PyQt6.QtGui import QPixmap
        
        # Constants for error messages
        ERROR_LOADING_IMAGE = "Failed to load image data"
        
        # Format sector name to be URL-safe
        formatted_sector = sector_name.replace(' ', '%20')
        
        # Use the data API endpoint for better reliability
        url = f"{self.base_url}/data/{formatted_sector}/image"
        params = {}
        
        # Use provided milieu or instance default
        current_milieu = milieu or self.milieu
        if current_milieu:
            params["milieu"] = current_milieu
        
        # Set default options if none provided
        if not options:
            options = {
                "style": "poster",
                "scale": 64,
                "options": "grid"
            }
        
        # Add options to params
        params.update(options)
        
        try:
            print(f"Fetching sector map for {sector_name} with URL: {url} and params: {params}")
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raises HTTPError for bad responses
            
            # Load the image data into a QPixmap
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                return pixmap, None
            else:
                print(ERROR_LOADING_IMAGE)
                return None, ERROR_LOADING_IMAGE
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error downloading sector map: {str(e)}"
            print(error_msg)
            return None, error_msg
        except Exception as e:
            return None, f"Error: {str(e)}"
            
    def get_system_jump_map(self, sector_name, hex_code, milieu: Optional[str] = None, options: Dict[str, Any] = None):
        """
        Retrieves a system jump map using the jumpmap API endpoint.
        Endpoint: https://travellermap.com/api/jumpmap
        
        Args:
            sector_name: Name or abbreviation of the sector
            hex_code: Hex code of the system (e.g., '1910')
            milieu: Optional milieu code (e.g., 'M1105', 'IW'). If None, uses the instance default.
            options: Optional dictionary of rendering options:
                - jump: Jump distance (default: 2)
                - style: Map style (e.g., 'poster', 'print')
                - scale: Scale factor
                - options: Comma-separated list of options
                
        Returns: A tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        
        url = f"{self.base_url}/api/jumpmap"
        params = {"sector": sector_name, "hex": hex_code}
        
        # Use provided milieu or instance default
        if milieu or self.milieu:
            params["milieu"] = milieu or self.milieu
        
        # Add any provided options
        if options:
            for key, value in options.items():
                if value is not None:
                    params[key] = value
        else:
            # Default options for good-looking maps
            params["jump"] = 2
            params["style"] = "poster"
            params["options"] = "grid,border,routes,names,worlds"
        
        try:
            response = requests.get(url, params=params, stream=True)
            if response.status_code != 200:
                return None, f"Error fetching system jump map: HTTP {response.status_code}"
                
            # Convert response content to QPixmap
            image_data = QByteArray(response.content)
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                return pixmap, None
            else:
                return None, "Failed to load image data"
        except Exception as e:
            return None, f"Error: {str(e)}"
            
    def get_planet_image(self, sector_name, hex_code, uwp, options: Dict[str, Any] = None):
        """
        Retrieves a planet image based on UWP data.
        Endpoint: https://travellermap.com/data/{sector}/hex/image
        
        Args:
            sector_name: Name or abbreviation of the sector
            hex_code: Hex code of the system (e.g., '1910')
            uwp: Universal World Profile string
            options: Optional dictionary of rendering options:
                - type: Image type (e.g., 'classic', 'atlas')
                - scale: Scale factor
                
        Returns: A tuple of (QPixmap, error_message). If successful, error_message will be None.
        """
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QByteArray
        
        # Format sector name for URL
        formatted_sector = sector_name.replace(' ', '')
        url = f"{self.base_url}/data/{formatted_sector}/{hex_code}/image"
        params = {}
        
        # Add UWP if provided
        if uwp:
            params["uwp"] = uwp
        
        # Add any provided options
        if options:
            for key, value in options.items():
                if value is not None:
                    params[key] = value
        else:
            # Default options
            params["type"] = "atlas"
            params["scale"] = 2
        
        try:
            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()  # Raises HTTPError for bad responses
            
            # Convert response content to QPixmap
            image_data = QByteArray(response.content)
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                return pixmap, None
            else:
                print(ERROR_LOADING_IMAGE)
                return None, ERROR_LOADING_IMAGE
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error downloading planet image: {str(e)}"
            print(error_msg)
            return None, error_msg
    
    # (Other endpoint methods omitted for brevity.)

# Example usage:
if __name__ == "__main__":
    api = TravellerMapAPI()
    try:
        # Retrieve the universe data.
        universe_json = api.get_universe()
        print("Universe data (partial):", json.dumps(universe_json, indent=2)[:500] + "...")
        
        # Extract the sectors list.
        if not (isinstance(universe_json, dict) and "Sectors" in universe_json):
            raise ValueError("Universe data does not contain 'Sectors'.")
        sectors_list = universe_json["Sectors"]
        
        # Extract sector names from each entry.
        sector_names = []
        for sector_entry in sectors_list:
            if isinstance(sector_entry, dict):
                # Try to extract the name from the first element in the "Names" list.
                name = ""
                if "Names" in sector_entry and isinstance(sector_entry["Names"], list) and sector_entry["Names"]:
                    name = sector_entry["Names"][0].get("Text", "")
                if not name:
                    name = sector_entry.get("Abbreviation", "")
                if name:
                    sector_names.append(name)
        
        print("Retrieved sectors: " + ", ".join(sector_names))
        
        # Process each sector.
        for sector_entry in sectors_list:
            if not isinstance(sector_entry, dict):
                continue
            
            # Extract the sector name.
            sector_name = ""
            if "Names" in sector_entry and isinstance(sector_entry["Names"], list) and sector_entry["Names"]:
                sector_name = sector_entry["Names"][0].get("Text", "")
            if not sector_name:
                sector_name = sector_entry.get("Abbreviation", "")
            if not sector_name:
                print("Skipping sector due to missing name/abbreviation.")
                continue
            
            print(f"\nProcessing sector: {sector_name}")
            
            # Get sector T5 data (showing only a truncated portion).
            try:
                t5_data = api.get_sector_t5(sector_name)
                display_data = t5_data[:200] + "..." if len(t5_data) > 200 else t5_data
                print("Sector T5 data:", display_data)
            except requests.exceptions.RequestException as e:
                print(f"Error getting T5 data for sector '{sector_name}': {e}")
            
            # Download sector map image.
            try:
                image_path = api.download_sector_image(sector_name)
                print("Sector image saved at:", image_path)
            except (requests.exceptions.RequestException, IOError) as e:
                print(f"Error downloading sector image for '{sector_name}':", e)
            
            # (Additional processing can be added here.)

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"Error: {e}")
    except Exception as e:  # Keep a generic exception as last resort
        print(f"Unexpected error: {e}")
