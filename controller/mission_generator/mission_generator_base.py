"""
Base Mission Generator for Traveller RPG campaigns.

This module provides the core MissionGenerator class that orchestrates
the mission generation process.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from model.mission_db_manager import MissionDBManager
from model.mission import Mission, MissionParticulars, MissionDetail, MissionReference
from .openai_client import get_openai_client, OPENAI_AVAILABLE
from .game_planner import GamePlannerTables
from .mission_particulars import generate_mission_particulars
from .image_generation import generate_vtt_map_image, generate_npc_images, generate_item_images
from .uwp_analyzer import uwp_summary

# Constants for frequently used strings
DEFAULT_MISSION_PARTICULARS = "Mission particulars not available."
OPENAI_UNAVAILABLE_MSG = "OpenAI client not available. Skipping operation."
UNKNOWN_WORLD = "unknown world"
UNKNOWN_SCENARIO = "unknown scenario"
OPENAI_API_KEY_LOADED_MSG = "OpenAI API key loaded successfully"
NO_OPENAI_API_KEY_FOUND_MSG = "No OpenAI API key found"
GPT_ENHANCED_MISSIONS_UNAVAILABLE_MSG = "GPT-enhanced missions will be unavailable"

# Set up logger
logger = logging.getLogger(__name__)


class MissionGenerator:
    """
    Generates random missions for Traveller RPG campaigns using the gamePlanner tables,
    UWP data, and optionally enhances them using ChatGPT API.
    """
    
    def __init__(self):
        """Initialize the mission generator."""
        # Load environment variables from multiple potential locations
        load_dotenv()  # Default .env file
        load_dotenv("tasj.env")  # Project-specific env file
        load_dotenv("config/.env")  # Config directory env file
        
        # Set up OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and OPENAI_AVAILABLE:
            self.gpt_available = True
            logger.info(OPENAI_API_KEY_LOADED_MSG)
        else:
            self.gpt_available = False
            if not OPENAI_AVAILABLE:
                logger.warning(f"{OPENAI_UNAVAILABLE_MSG} {GPT_ENHANCED_MISSIONS_UNAVAILABLE_MSG}")
            elif not self.api_key:
                logger.warning(f"{NO_OPENAI_API_KEY_FOUND_MSG}. {GPT_ENHANCED_MISSIONS_UNAVAILABLE_MSG}")
                
        # Initialize the mission database manager
        self.db_manager = MissionDBManager()
        
        # Load game planner tables
        self.game_planner = GamePlannerTables()
        self.game_planner_tables = self.game_planner.load_tables()
        
        # Initialize worlds list (would be populated from database in real implementation)
        self.worlds = []
                
    def generate_mission_structure(self) -> Dict[str, Any]:
        """
        Generate a basic mission structure with scenario type, details, and references.
        
        Returns:
            Mission object containing the basic mission structure
        """
        # Create a new Mission object with minimal required fields
        mission = Mission(
            world={},
            scenario_type={},
            particulars=MissionParticulars()
        )
        
        # Roll for scenario type (PHASE 1, Table 1)
        scenario_name, scenario_id, reference_table = self.game_planner.roll_on_table("PHASE 1", "1")
        mission.scenario_type = {"name": scenario_name, "id": scenario_id}
        
        # Process references to build details
        details = {}
        references = []
        
        # Follow reference chain if available
        current_phase = "PHASE 1"
        current_table = reference_table
        
        while current_table:
            # Roll on the referenced table
            detail_name, detail_id, next_reference = self.game_planner.roll_on_table(current_phase, current_table)
            
            # Add to details
            table_info = self.game_planner.get_table_info(current_phase, current_table)
            table_name = table_info.get("name", f"Table {current_table}")
            
            # Create a MissionDetail
            detail = MissionDetail(
                detail_type=table_name,
                detail_name=detail_name,
                detail_id=detail_id
            )
            details[table_name] = detail
            
            # Add reference
            reference = MissionReference(
                phase=current_phase,
                table_id=current_table,
                result=detail_name
            )
            references.append(reference)
            
            # Move to next reference if available
            current_table = next_reference
            
            # If we're moving to a new phase
            if current_table and current_table.startswith("PHASE"):
                parts = current_table.split()
                if len(parts) >= 2:
                    current_phase = f"{parts[0]} {parts[1]}"
                    current_table = parts[2] if len(parts) > 2 else None
        
        # Set details and references in the mission
        mission.details = details
        mission.references = references
        
        return mission
        
    def generate_mission_for_world(self, world_data: Dict[str, Any], use_gpt: bool = True) -> Mission:
        """
        Generate a complete mission for a specific world, using UWP data to inform the mission structure.
        
        Args:
            world_data: Dict containing world information including UWP
            use_gpt: Whether to enhance the mission with GPT
            
        Returns:
            Mission object containing the complete mission data
        """
        # Generate basic mission structure
        mission = self.generate_mission_structure()
        
        # Add world data
        mission.world = world_data
        
        # Adjust mission based on UWP data
        self._adjust_mission_based_on_uwp(mission)
        
        # Generate map description
        mission.map_description = self._generate_map_description(mission, use_gpt)
        
        # Generate mission particulars
        mission.particulars = generate_mission_particulars(mission, use_gpt, self.gpt_available, self.api_key)
        
        # Generate images if GPT is available
        if use_gpt and self.gpt_available:
            # Generate map image
            map_image_url = generate_vtt_map_image(mission, self.api_key)
            if map_image_url:
                mission.particulars.map_image = map_image_url
                
            # Generate NPC images
            npc_image_urls = generate_npc_images(mission, self.api_key)
            if npc_image_urls:
                mission.particulars.npc_images = npc_image_urls
                
            # Generate item images
            item_image_urls = generate_item_images(mission, self.api_key)
            if item_image_urls:
                mission.particulars.item_images = item_image_urls
        
        # Save mission to database
        saved_mission = self.db_manager.save_mission(mission)
        
        return saved_mission
    
    def _adjust_mission_based_on_uwp(self, mission: Mission):
        """
        Adjust mission details based on the world's UWP data.
        
        Args:
            mission: The Mission object containing world information
        """
        if not mission.world or "UWP" not in mission.world:
            return
            
        uwp = mission.world.get("UWP", "")
        
        # Extract UWP components
        if len(uwp) >= 9:
            starport = uwp[0]
            size = uwp[1]
            atmosphere = uwp[2]
            hydrographics = uwp[3]
            population = uwp[4]
            government = uwp[5]
            law_level = uwp[6]
            tech_level = uwp[8] if len(uwp) > 8 else "0"
            
            # Set UWP factors in mission
            mission.uwp_factors = {
                "starport": starport,
                "size": size,
                "atmosphere": atmosphere,
                "hydrographics": hydrographics,
                "population": population,
                "government": government,
                "law_level": law_level,
                "tech_level": tech_level
            }
            
            # Determine tech context
            tech_level_num = ord(tech_level) - ord('0') if tech_level.isdigit() else 0
            if tech_level_num <= 4:
                mission.tech_context = "low tech"
            elif tech_level_num <= 9:
                mission.tech_context = "moderate tech"
            elif tech_level_num <= 12:
                mission.tech_context = "high tech"
            else:
                mission.tech_context = "very high tech"
                
            # Determine population density
            pop_level = ord(population) - ord('0') if population.isdigit() else 0
            if pop_level <= 3:
                mission.population_density = "sparse population"
            elif pop_level <= 6:
                mission.population_density = "moderate population"
            elif pop_level <= 9:
                mission.population_density = "dense population"
            else:
                mission.population_density = "teeming megacities"
                
            # Determine port context
            if starport in "AB":
                mission.port_context = "major starport"
            elif starport in "CD":
                mission.port_context = "minor starport"
            else:
                mission.port_context = "primitive landing area"
                
            # Determine environment
            atmo_level = ord(atmosphere) - ord('0') if atmosphere.isdigit() else 0
            hydro_level = ord(hydrographics) - ord('0') if hydrographics.isdigit() else 0
            
            if atmo_level in [0, 1, 2, 3, 10, 11, 12, 13, 14, 15]:
                mission.environment = "hostile environment"
            elif hydro_level >= 8:
                mission.environment = "water world"
            elif hydro_level <= 2:
                mission.environment = "desert world"
            else:
                mission.environment = "habitable world"
                
            # Determine law context
            law_level_num = ord(law_level) - ord('0') if law_level.isdigit() else 0
            if law_level_num <= 3:
                mission.law_context = "low law"
            elif law_level_num <= 6:
                mission.law_context = "moderate law"
            elif law_level_num <= 9:
                mission.law_context = "high law"
            else:
                mission.law_context = "extreme law"
    
    def _generate_map_description(self, mission: Mission, use_gpt: bool) -> str:
        """
        Generate a description for a VTT map based on the mission.
        
        Args:
            mission: The Mission object
            use_gpt: Whether to use GPT to enhance the description
            
        Returns:
            A string containing the map description
        """
        # Start with basic description based on mission type
        scenario_type = mission.scenario_type.get("name", UNKNOWN_SCENARIO)
        world_name = mission.world.get("name", UNKNOWN_WORLD)
        
        base_description = f"Map for {scenario_type} mission on {world_name}."
        
        # Add environment context
        if hasattr(mission, 'environment') and mission.environment:
            base_description += f" {mission.environment.capitalize()}."
            
        # Add population context
        if hasattr(mission, 'population_density') and mission.population_density:
            base_description += f" {mission.population_density.capitalize()}."
            
        # Add tech context
        if hasattr(mission, 'tech_context') and mission.tech_context:
            base_description += f" {mission.tech_context.capitalize()} level."
            
        # If GPT is available and requested, enhance the description
        if use_gpt and self.gpt_available:
            client = get_openai_client(self.api_key)
            if not client:
                logger.warning(OPENAI_UNAVAILABLE_MSG)
                return base_description
                
            try:
                # Prepare prompt for GPT
                prompt = f"""Create a detailed map description for a virtual tabletop (VTT) Traveller RPG session.
                Mission: {scenario_type}
                World: {world_name}
                Environment: {getattr(mission, 'environment', 'unknown')}
                Population: {getattr(mission, 'population_density', 'unknown')}
                Tech Level: {getattr(mission, 'tech_context', 'unknown')}
                
                Describe the key locations, terrain features, and points of interest that would be relevant for this mission.
                Keep it under 150 words."""
                
                # Call GPT API
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant creating content for a Traveller RPG campaign."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200
                )
                
                # Extract and return the enhanced description
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                    
            except Exception as e:
                logger.error(f"Error generating map description with GPT: {e}")
                
        return base_description
    
    def get_missions_for_world(self, world_id: int) -> List[Mission]:
        """
        Get all missions for a specific world from the database.
        
        Args:
            world_id: The ID of the world
            
        Returns:
            List of mission data
        """
        try:
            return self.db_manager.get_missions_for_world(world_id)
        except Exception as e:
            logger.error(f"Error retrieving missions for world {world_id} from database: {e}")
            return []
    
    def generate_multiple_missions(self, world_data: Dict[str, Any], count: int = 3, use_gpt: bool = True) -> List[Mission]:
        """
        Generate multiple missions for a specific world.
        
        Args:
            world_data: Dict containing world information
            count: Number of missions to generate
            use_gpt: Whether to enhance missions with GPT
            
        Returns:
            List of mission objects
        """
        missions = []
        
        for _ in range(count):
            mission = self.generate_mission_for_world(world_data, use_gpt)
            missions.append(mission)
        
        return missions
    
    def get_available_worlds(self) -> List[Dict[str, Any]]:
        """
        Get the list of available worlds.
        
        Returns:
            List of world dicts
        """
        # In a real implementation, this would fetch worlds from the database
        return self.worlds
