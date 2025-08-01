import os
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

class SectorMapLoader:
    """Handles downloading and caching sector maps from the Traveller Map API."""
    
    BASE_URL = "https://travellermap.com"
    
    def __init__(self, cache_dir: str = "data/sector_maps"):
        """Initialize with cache directory.
        
        Args:
            cache_dir: Directory to store downloaded sector maps
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_sector_map_path(self, sector_name: str, milieu: str = "M1105") -> Optional[str]:
        """Get the path to a sector map, downloading it if necessary.
        
        Args:
            sector_name: Name of the sector (e.g., 'Spinward Marches')
            milieu: The era/milieu (default: 'M1105' for 1105 Imperial)
            
        Returns:
            Path to the sector map image, or None if download failed
        """
        # Create a safe filename from sector name
        safe_name = "".join(c if c.isalnum() else "_" for c in sector_name).strip("_")
        file_path = self.cache_dir / f"{milieu}_{safe_name}.png"
        
        # Return cached file if it exists
        if file_path.exists():
            return str(file_path)
            
        # Download the sector map using the poster API
        params = {
            "sector": sector_name,
            "milieu": milieu,
            "style": "poster",  # Clean style without borders
            "scale": 48,  # Higher resolution (48px per hex)
            "options": "0x0001"  # Show hex grid
        }
        
        try:
            # Use the poster API endpoint
            url = f"{self.BASE_URL}/api/poster"
            response = requests.get(
                url,
                params=params,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # Save the image
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return str(file_path)
            
        except Exception as e:
            print(f"Error downloading sector map for {sector_name}: {e}")
            print(f"URL: {response.url if 'response' in locals() else 'N/A'}")
            # Clean up if we created a file but the download failed
            if file_path.exists():
                file_path.unlink()
            return None
