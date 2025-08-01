# In controller/planets_controller.py

import logging
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from view.planet_view import PlanetView
from controller.mission_generator import MissionGenerator
from model.planet_map_manager import PlanetMapManager
# Import removed - PlanetGenerator doesn't exist
# Using sample planet data instead

logger = logging.getLogger(__name__)

class PlanetController:
    """Controller for planet/system view and related functionality."""
    
    def __init__(self, db_instance):
        """Initialize the planet controller."""
        self.db = db_instance
        self.view = None
        self.mission_generator = MissionGenerator()
        self.current_planet = None
        self.missions = []
        self.current_sector_id = None
        
        # Get database path for map storage
        self.db_path = getattr(db_instance, 'db_path', ':memory:')
        self.map_manager = PlanetMapManager(self.db_path)
    
    def show_view(self, parent_widget=None) -> QWidget:
        """Create and return the planet view."""
        self.view = PlanetView(parent_widget)
        
        # Connect signals
        self.view.mission_generation_requested.connect(self._handle_mission_generation)
        self.view.mission_selected.connect(self._handle_mission_selected)
        self.view.map_generation_requested.connect(self._handle_map_generation)
        
        # Initialize the planet map widget with database path
        self.view.planet_map.set_db_path(self.db_path)
        
        # Load planets from database
        self._load_planets()
        
        return self.view
    
    def set_current_sector(self, sector_data: Dict[str, Any]):
        """Set the current sector and load its planets.
        
        Args:
            sector_data: Dictionary containing sector information.
        """
        if not sector_data or 'sector_id' not in sector_data:
            logger.error("Invalid sector data provided")
            return
            
        self.current_sector_id = sector_data['sector_id']
        
        # If the planet view is already showing, update it with the new sector's planets
        if self.view and self.view.isVisible():
            self._load_planets_for_sector(self.current_sector_id)
            
    def _load_planets_for_sector(self, sector_id: int):
        """Load planets for the specified sector from the database.
        
        Args:
            sector_id: ID of the sector to load planets for.
        """
        try:
            # Query planets for this sector from the database
            planets = self.db.read_records("planets", {"sector_id": sector_id})
            
            if not planets:
                # No planets found for this sector
                self.view.set_planet(None)
                self.view.planet_header.setText("No planets found for this sector")
                return
                
            # Convert the first planet to a dictionary for the view
            planet = planets[0]
            planet_dict = {
                "planet_id": planet[0],
                "name": planet[1],
                "sector_id": planet[2],
                "x_coordinate": planet[3],
                "y_coordinate": planet[4],
                "UPP": planet[5],
                "description": planet[6],
                "image_path": planet[7],
                "starport": planet[8],
                "size": planet[9],
                "atmosphere": planet[10],
                "hydrographics": planet[11],
                "population": planet[12],
                "government": planet[13],
                "law_level": planet[14],
                "tech_level": planet[15],
                "allegiance": planet[16],
                "stellar": planet[17],
                "gas_giant": planet[18],
                "bases": planet[19],
                "trade_codes": planet[20].split(',') if planet[20] else [],
                "travel_code": planet[21],
                "importance": planet[22],
                "economic": planet[23],
                "hex": planet[24],
                "subsector_id": planet[25],
                "travel_zone": planet[26],
                "pbg": planet[27],
                "UWP": planet[28]
            }
            
            # Set the current planet and update the view
            self.set_planet(planet_dict)
            
        except Exception as e:
            logger.error(f"Error loading planets for sector {sector_id}: {e}")
            self.view.planet_header.setText(f"Error loading planets: {str(e)}")
            self.view.planet_details.setText(f"Failed to load planets: {str(e)}")
            
    def _load_planets(self):
        """Load planets from database."""
        try:
            # Query planets from the database
            planets = self.db.read_records("planets")
            
            if not planets:
                # No planets found
                self.view.set_planet(None)
                self.view.planet_header.setText("No planets found")
                return
                
            # If no planets in database, create a sample planet for testing
            sample_planet = {
                "name": "Fermi",
                "UWP": "A867954-D",
                "trade_codes": ["Hi", "Ri", "In"],
                "description": "Fermi is a high-tech industrial world with a rich economy and advanced research facilities."
            }
            
            self.current_planet = sample_planet
            if self.view:
                self.view.set_planet(sample_planet)
                
                # Load missions for this planet
                self._load_missions_for_planet(sample_planet)
                
        except Exception as e:
            logger.error(f"Error loading planets: {e}")
    
    def _load_missions_for_planet(self, planet: Dict[str, Any]):
        """Load missions for the specified planet."""
        try:
            # In a real implementation, you would query the database for missions
            # associated with this planet
            
            # For now, generate some sample missions
            missions = self.mission_generator.generate_multiple_missions(
                world_data=planet,
                count=2,  # Start with 2 missions
                use_gpt=False  # Don't use GPT for initial load to be faster
            )
            
            # Convert Mission objects to dictionaries for the view
            self.missions = []
            for mission in missions:
                if hasattr(mission, 'to_dict') and callable(mission.to_dict):
                    # It's a Mission object with to_dict method
                    self.missions.append(mission.to_dict())
                elif hasattr(mission, '__dict__'):
                    # It's a Mission object without to_dict method
                    mission_dict = mission.__dict__.copy()
                    # Handle nested objects like particulars
                    if hasattr(mission, 'particulars') and hasattr(mission.particulars, '__dict__'):
                        mission_dict['particulars'] = mission.particulars.__dict__.copy()
                    self.missions.append(mission_dict)
                else:
                    # It's already a dict
                    self.missions.append(mission)
            
            if self.view:
                self.view.set_missions(self.missions)
                
        except Exception as e:
            # Get planet name safely
            planet_name = planet.get('name', 'Unknown') if isinstance(planet, dict) else getattr(planet, 'name', 'Unknown')
            logger.error(f"Error loading missions for planet {planet_name}: {e}")
    
    def _handle_mission_generation(self, params: Dict[str, Any]):
        """Handle mission generation request from the view."""
        try:
            world = params.get("world")
            count = params.get("count", 3)
            use_gpt = params.get("use_gpt", True)
            
            if not world:
                logger.error("No world specified for mission generation")
                return
            
            # Generate missions
            new_missions = self.mission_generator.generate_multiple_missions(
                world_data=world,
                count=count,
                use_gpt=use_gpt
            )
            
            # Convert Mission objects to dictionaries for the view
            mission_dicts = []
            for mission in new_missions:
                if hasattr(mission, '__dict__'):
                    # It's a Mission object, convert to dict
                    mission_dict = mission.__dict__.copy()
                    # Handle nested objects like particulars
                    if hasattr(mission, 'particulars') and hasattr(mission.particulars, '__dict__'):
                        mission_dict['particulars'] = mission.particulars.__dict__.copy()
                    mission_dicts.append(mission_dict)
                else:
                    # It's already a dict
                    mission_dicts.append(mission)
            
            # Add to existing missions
            self.missions.extend(mission_dicts)
            
            # Update the view
            if self.view:
                self.view.set_missions(self.missions)
                
        except Exception as e:
            logger.error(f"Error generating missions: {e}")
    
    def _handle_mission_selected(self, mission):
        """Handle mission selection from the view."""
        try:
            # Import here to avoid circular imports
            from view.mission_detail_view import MissionDetailView
            
            # Get mission title safely whether it's a dict or Mission object
            if hasattr(mission, '__dict__'):
                # It's a Mission object
                title = getattr(mission, 'title', 'Unknown mission')
            else:
                # It's a dictionary
                title = mission.get('title', 'Unknown mission')
                
            logger.info(f"Mission selected: {title}")
            
            # Create and show mission detail view
            self.mission_detail_view = MissionDetailView(self.view)
            self.mission_detail_view.set_mission(mission)
            self.mission_detail_view.mission_closed.connect(self._on_mission_detail_closed)
            self.mission_detail_view.show()
            
        except Exception as e:
            logger.error(f"Error handling mission selection: {e}")
    
    def _on_mission_detail_closed(self):
        """Handle mission detail view closed."""
        # Clean up the mission detail view
        if hasattr(self, 'mission_detail_view'):
            self.mission_detail_view = None
    
    def _handle_map_generation(self, params: Dict[str, Any]):
        """Handle map generation request from the view."""
        try:
            planet = params.get("planet")
            
            if not planet:
                logger.error("No planet specified for map generation")
                return
            
            logger.info(f"Generating map for planet: {planet.get('name')}")
            
            # The actual map generation is handled by the PlanetMapWidget
            # This method is just a hook for any additional controller logic
            # that might be needed when a map is generated
            
        except Exception as e:
            logger.error(f"Error handling map generation: {e}")
