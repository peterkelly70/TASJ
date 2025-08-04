#!/usr/bin/env python3
"""
Traveller Map Data Mapper

This module provides a mapper class that takes data from the Traveller Map API
and maps it to the appropriate database tables and models in the application.
"""

import os
import logging
import json
from datetime import datetime
from PyQt6.QtGui import QPixmap
from model.traveller_map_api_fixed_v2 import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TravellerMapDataMapper:
    """
    Maps data from the Traveller Map API to the appropriate database tables and models.
    """
    
    def __init__(self, api_client=None):
        """
        Initialize the Traveller Map Data Mapper.
        
        Args:
            api_client: Optional TravellerMapAPI instance to use
        """
        self.api_client = api_client or TravellerMapAPI()
        
    def fetch_and_map_sector(self, sector_name, milieu=None):
        """
        Fetch sector data from the API and map it to the database.
        
        Args:
            sector_name: Name of the sector to fetch
            milieu: Optional milieu code
            
        Returns:
            Dictionary with mapped sector data
        """
        logger.info(f"Fetching and mapping sector data for {sector_name}")
        
        # Fetch sector data from API
        sector_data = self.api_client.get_sector_data(sector_name, milieu)
        if not sector_data:
            logger.error(f"Failed to fetch sector data for {sector_name}")
            return None
            
        # Map sector metadata
        mapped_sector = self._map_sector_metadata(sector_data.get('metadata', {}))
        mapped_sector['name'] = sector_name
        
        # Map sector systems
        mapped_sector['systems'] = self._map_systems(sector_data.get('systems', []))
        
        # Fetch and map sector image
        sector_pixmap, error = self.api_client.get_sector_pixmap(sector_name, milieu)
        if sector_pixmap and not error:
            mapped_sector['image_path'] = self.api_client.save_sector_image(sector_name, milieu)
            mapped_sector['image'] = sector_pixmap
        else:
            logger.warning(f"Failed to fetch sector image: {error}")
            mapped_sector['image_path'] = None
            mapped_sector['image'] = None
            
        return mapped_sector
        
    def fetch_and_map_system(self, sector_name, hex_code, milieu=None):
        """
        Fetch system data from the API and map it to the database.
        
        Args:
            sector_name: Name of the sector
            hex_code: Hex code of the system
            milieu: Optional milieu code
            
        Returns:
            Dictionary with mapped system data
        """
        logger.info(f"Fetching and mapping system data for {sector_name} {hex_code}")
        
        # Fetch sector data from API to get the system
        sector_data = self.api_client.get_sector_data(sector_name, milieu)
        if not sector_data:
            logger.error(f"Failed to fetch sector data for {sector_name}")
            return None
            
        # Find the system in the sector data
        system = None
        for s in sector_data.get('systems', []):
            if s.get('hex') == hex_code:
                system = s
                break
                
        if not system:
            logger.error(f"System {hex_code} not found in sector {sector_name}")
            return None
            
        # Map system data
        mapped_system = self._map_system(system)
        mapped_system['sector_name'] = sector_name
        
        # Fetch and map system image
        system_pixmap, error = self.api_client.get_system_pixmap(sector_name, hex_code, milieu)
        if system_pixmap and not error:
            mapped_system['image_path'] = self.api_client.save_system_image(sector_name, hex_code, milieu)
            mapped_system['image'] = system_pixmap
        else:
            logger.warning(f"Failed to fetch system image: {error}")
            mapped_system['image_path'] = None
            mapped_system['image'] = None
            
        return mapped_system
        
    def _extract_field(self, item, field_names):
        """
        Extract a field from an item using multiple possible field names.
        
        Args:
            item: Dictionary containing the data
            field_names: List of possible field names to check
            
        Returns:
            The field value if found, or empty string
        """
        for name in field_names:
            if name in item and item[name]:
                return item[name]
        return ''
    
    def search_and_map_results(self, query):
        """
        Search for systems and map the results.
        
        Args:
            query: Search query string
            
        Returns:
            List of mapped search results
        """
        logger.info(f"Searching and mapping results for query: {query}")
        
        # Perform search
        search_results = self.api_client.search(query)
        if not search_results or 'Results' not in search_results:
            logger.error(f"Failed to search for {query}")
            return []
            
        # Map search results
        mapped_results = []
        items = search_results.get('Results', {}).get('Items', [])
        
        for item in items:
            # Handle nested structure - each item contains either 'World' or 'Subsector'
            if 'World' in item:
                mapped_result = self._map_world_search_result(item['World'])
            elif 'Subsector' in item:
                mapped_result = self._map_subsector_search_result(item['Subsector'])
            else:
                # Try to map directly if no nested structure
                mapped_result = self._map_generic_search_result(item)
                
            # Only add results that have at least a name or hex code
            if mapped_result.get('name') or mapped_result.get('hex'):
                mapped_results.append(mapped_result)
            
        return mapped_results
        
    def _map_world_search_result(self, world):
        """
        Map a world search result to the database schema.
        
        Args:
            world: World data from the search API
            
        Returns:
            Dictionary with mapped world data
        """
        # Extract hex coordinates if available
        hex_code = ''
        if 'HexX' in world and 'HexY' in world:
            hex_x = world.get('HexX')
            hex_y = world.get('HexY')
            if hex_x is not None and hex_y is not None:
                # Format as standard hex code (e.g., '1910')
                hex_code = f"{hex_x:02d}{hex_y:02d}"
        
        # Create mapped result
        mapped_result = {
            'name': world.get('Name', ''),
            'sector': world.get('Sector', ''),
            'hex': hex_code,
            'uwp': world.get('Uwp', ''),
            'type': 'World',
            'sector_x': world.get('SectorX'),
            'sector_y': world.get('SectorY'),
            'sector_tags': world.get('SectorTags', '')
        }
        
        # Parse UWP if available
        if mapped_result['uwp']:
            uwp_components = self._parse_uwp(mapped_result['uwp'])
            mapped_result.update(uwp_components)
            
        return mapped_result
        
    def _map_subsector_search_result(self, subsector):
        """
        Map a subsector search result to the database schema.
        
        Args:
            subsector: Subsector data from the search API
            
        Returns:
            Dictionary with mapped subsector data
        """
        return {
            'name': subsector.get('Name', ''),
            'sector': subsector.get('Sector', ''),
            'type': 'Subsector',
            'index': subsector.get('Index', ''),
            'sector_x': subsector.get('SectorX'),
            'sector_y': subsector.get('SectorY'),
            'sector_tags': subsector.get('SectorTags', '')
        }
        
    def _map_generic_search_result(self, item):
        """
        Map a generic search result to the database schema.
        
        Args:
            item: Generic data from the search API
            
        Returns:
            Dictionary with mapped data
        """
        # Extract fields using helper method
        name = self._extract_field(item, ['Name', 'Text', 'WorldName'])
        sector = self._extract_field(item, ['Sector', 'SectorName'])
        hex_code = self._extract_field(item, ['Hex', 'HexCode'])
        uwp = self._extract_field(item, ['UWP', 'Uwp'])
        
        # Create mapped result
        mapped_result = {
            'name': name,
            'sector': sector,
            'hex': hex_code,
            'uwp': uwp,
            'type': item.get('Type', 'Unknown')
        }
        
        # Add coordinates if available
        if 'X' in item and 'Y' in item:
            mapped_result['coordinates'] = {
                'x': item.get('X'),
                'y': item.get('Y')
            }
                
        # Add any other fields that might be in the result
        for key, value in item.items():
            if key.lower() not in mapped_result and key not in ['X', 'Y', 'Text', 'SectorName', 'HexCode']:
                mapped_result[key.lower()] = value
                
        return mapped_result
        
    def get_available_milieux(self):
        """
        Get available milieux from the API.
        
        Returns:
            List of mapped milieux
        """
        logger.info("Fetching available milieux")
        
        # Fetch milieux
        milieux = self.api_client.get_available_milieux()
        if not milieux:
            logger.error("Failed to fetch milieux")
            return []
            
        # Map milieux
        mapped_milieux = []
        for milieu in milieux:
            mapped_milieu = {
                'code': milieu.get('Code', ''),
                'name': milieu.get('Name', ''),
                'is_default': milieu.get('IsDefault', False)
            }
            mapped_milieux.append(mapped_milieu)
            
        return mapped_milieux
        
    def _map_sector_metadata(self, metadata):
        """
        Map sector metadata to the database schema.
        
        Args:
            metadata: Sector metadata from the API
            
        Returns:
            Dictionary with mapped sector metadata
        """
        return {
            'abbreviation': metadata.get('Abbreviation', ''),
            'names': metadata.get('Names', []),
            'x': metadata.get('X', 0),
            'y': metadata.get('Y', 0),
            'subsectors': self._map_subsectors(metadata.get('Subsectors', [])),
            'allegiances': metadata.get('Allegiances', {}),
            'borders': metadata.get('Borders', []),
            'routes': metadata.get('Routes', []),
            'labels': metadata.get('Labels', []),
            'credits': metadata.get('Credits', ''),
            'tags': metadata.get('Tags', []),
            'data_file': metadata.get('DataFile', ''),
            'products': metadata.get('Products', []),
            'stylesheet': metadata.get('Stylesheet', ''),
            'regions': metadata.get('Regions', []),
            'last_updated': datetime.now().isoformat()
        }
        
    def _map_subsectors(self, subsectors):
        """
        Map subsector data to the database schema.
        
        Args:
            subsectors: List of subsectors from the API
            
        Returns:
            Dictionary with mapped subsectors
        """
        mapped_subsectors = {}
        for subsector in subsectors:
            index = subsector.get('Index', '')
            mapped_subsectors[index] = {
                'name': subsector.get('Name', ''),
                'index': index,
                'x': subsector.get('X', 0),
                'y': subsector.get('Y', 0)
            }
        return mapped_subsectors
        
    def _map_systems(self, systems):
        """
        Map system data to the database schema.
        
        Args:
            systems: List of systems from the API
            
        Returns:
            List of mapped systems
        """
        return [self._map_system(system) for system in systems]
        
    def _map_system(self, system):
        """
        Map a single system to the database schema.
        
        Args:
            system: System data from the API
            
        Returns:
            Dictionary with mapped system data
        """
        # Extract UWP components if available
        uwp = system.get('uwp', '')
        uwp_components = self._parse_uwp(uwp)
        
        return {
            'hex': system.get('hex', ''),
            'name': system.get('name', ''),
            'uwp': uwp,
            'starport': uwp_components.get('starport', ''),
            'size': uwp_components.get('size', ''),
            'atmosphere': uwp_components.get('atmosphere', ''),
            'hydrographics': uwp_components.get('hydrographics', ''),
            'population': uwp_components.get('population', ''),
            'government': uwp_components.get('government', ''),
            'law_level': uwp_components.get('law_level', ''),
            'tech_level': uwp_components.get('tech_level', ''),
            'bases': system.get('bases', ''),
            'trade_codes': system.get('trade_codes', []),
            'travel_code': system.get('travel_code', ''),
            'zone': system.get('zone', ''),
            'pbg': system.get('pbg', ''),
            'allegiance': system.get('allegiance', ''),
            'stellar': system.get('stellar', ''),
            'x': system.get('x', 0),
            'y': system.get('y', 0),
            'subsector': system.get('subsector', ''),
            'importance': system.get('importance', 0),
            'economic': system.get('economic', ''),
            'cultural': system.get('cultural', ''),
            'nobles': system.get('nobles', ''),
            'worlds': system.get('worlds', ''),
            'resource_units': system.get('ru', 0),
            'last_updated': datetime.now().isoformat()
        }
        
    def _parse_uwp(self, uwp):
        """
        Parse a UWP string into its components.
        
        Args:
            uwp: UWP string (e.g., "A867969-D")
            
        Returns:
            Dictionary with UWP components
        """
        if not uwp:
            return {}
            
        # Handle different UWP formats
        components = {}
        
        # Standard UWP format (e.g., "A867969-D")
        if '-' in uwp and len(uwp) >= 9:
            self._parse_standard_uwp(uwp, components)
        # Short UWP format (e.g., "A7")
        elif len(uwp) == 2:
            components['starport'] = uwp[0]
            components['tech_level'] = uwp[1]
        # Other formats - just store as-is
        else:
            logger.warning(f"Unrecognized UWP format: {uwp}")
            components['raw_uwp'] = uwp
            
        return components
        
    def _parse_standard_uwp(self, uwp, components):
        """
        Parse a standard UWP string (e.g., "A867969-D") into components.
        
        Args:
            uwp: Standard UWP string
            components: Dictionary to populate with components
        """
        # Parse the first 7 characters
        components['starport'] = uwp[0] if len(uwp) > 0 else ''
        components['size'] = uwp[1] if len(uwp) > 1 else ''
        components['atmosphere'] = uwp[2] if len(uwp) > 2 else ''
        components['hydrographics'] = uwp[3] if len(uwp) > 3 else ''
        components['population'] = uwp[4] if len(uwp) > 4 else ''
        components['government'] = uwp[5] if len(uwp) > 5 else ''
        components['law_level'] = uwp[6] if len(uwp) > 6 else ''
        
        # Find tech level after the hyphen
        hyphen_pos = uwp.find('-')
        if hyphen_pos != -1 and hyphen_pos + 1 < len(uwp):
            components['tech_level'] = uwp[hyphen_pos + 1]
        else:
            components['tech_level'] = ''

    # This duplicate method was removed

# Example usage
if __name__ == "__main__":
    # Create mapper
    mapper = TravellerMapDataMapper()
    
    # Fetch and map sector data
    sector_name = "Spinward Marches"
    mapped_sector = mapper.fetch_and_map_sector(sector_name)
    
    if mapped_sector:
        print(f"Successfully mapped sector: {mapped_sector['name']}")
        print(f"Found {len(mapped_sector['systems'])} systems")
        
        # Print first system as example
        if mapped_sector['systems']:
            first_system = mapped_sector['systems'][0]
            print(f"First system: {first_system['hex']} {first_system['name']} {first_system['uwp']}")
            
        # Check if sector image was retrieved
        if mapped_sector['image']:
            print(f"Sector image size: {mapped_sector['image'].width()}x{mapped_sector['image'].height()}")
            print(f"Saved to: {mapped_sector['image_path']}")
        else:
            print("No sector image available")
    else:
        print(f"Failed to map sector {sector_name}")
