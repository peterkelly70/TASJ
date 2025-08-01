from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import re

@dataclass
class Planet:
    """Data class representing a planet in the Traveller universe.
    
    Required fields (validated in validate() method):
        - name: str - The name of the planet
        - sector_id: int - The ID of the sector this planet belongs to
        - x_coordinate: int - X coordinate in the sector (0-31)
        - y_coordinate: int - Y coordinate in the sector (0-40)
        - uwp: str - Universal World Profile (format: X123456-7)
    """
    name: Optional[str] = None
    sector_id: Optional[int] = None
    x_coordinate: Optional[int] = None
    y_coordinate: Optional[int] = None
    uwp: Optional[str] = None
    description: str = ""
    image_path: str = ""
    starport: str = ""
    size: str = ""
    atmosphere: str = ""
    hydrographics: str = ""
    population: str = ""
    government: str = ""
    law_level: str = ""
    tech_level: str = ""
    allegiance: str = ""
    stellar: str = ""
    gas_giant: bool = False
    bases: str = ""
    trade_codes: str = ""
    travel_code: str = ""
    importance: str = ""
    economic: str = ""
    hex: str = ""
    subsector_id: Optional[int] = None
    travel_zone: str = ""
    pbg: str = ""
    planet_id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Planet':
        """Create a Planet instance from a dictionary."""
        # Filter out any keys that aren't in the class's __annotations__
        valid_keys = {k for k in cls.__annotations__ if k != 'return'}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Planet instance to a dictionary."""
        return asdict(self)

    def validate(self) -> List[str]:
        """
        Validate the planet data.
        
        Returns:
            List[str]: List of error messages, empty if validation passes
        """
        errors = []
        
        # Required fields validation
        if not self.name or not str(self.name).strip():
            errors.append("Planet name is required.")
        
        # Only validate other fields if they are provided
        if self.uwp is not None:
            # UWP format validation (example: A123456-7)
            # First character: A-H, J-M, X, Y (starport)
            # Next 6 digits (world details)
            # Optional: - followed by a digit or letter (trade codes)
            if not re.match(r'^[A-HJ-MXY]\d{6}(?:-[\dA-Z])?$', str(self.uwp)):
                errors.append("Invalid UWP format. Expected format: X123456-7 or X123456-")
        
        # Coordinate validation if coordinates are provided
        if self.x_coordinate is not None and not (0 <= int(self.x_coordinate) <= 31):
            errors.append("X coordinate must be between 0 and 31.")
                
        if self.y_coordinate is not None and not (0 <= int(self.y_coordinate) <= 40):
            errors.append("Y coordinate must be between 0 and 40.")
        
        return errors
