import os
import json
import requests
from typing import Optional, List, Dict, Any

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
        Endpoint: https://travellermap.com/data/sector
        
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
