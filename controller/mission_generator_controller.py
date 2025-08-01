"""
Mission Generator Controller for Traveller RPG campaigns.

This module connects the mission generator model with the UI view
and handles the business logic for mission generation and management.
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QWidget

from controller.mission_generator import MissionGenerator
from view.mission_generator_view import MissionGeneratorView

logger = logging.getLogger(__name__)

class MissionGeneratorController:
    """Controller for the mission generator feature."""
    
    def __init__(self, parent_widget=None, db_controller=None):
        """
        Initialize the mission generator controller.
        
        Args:
            parent_widget: Parent widget for the view
            db_controller: Database controller for persistence
        """
        self.generator = MissionGenerator()
        self.view = MissionGeneratorView(parent_widget)
        self.db_controller = db_controller
        self.missions = []
        
        # Connect signals
        self.view.mission_generated.connect(self._handle_mission_generation)
        self.view.mission_saved.connect(self._handle_mission_save)
        
        # Initialize view with available worlds
        self._load_worlds()
    
    def _load_worlds(self):
        """Load available worlds into the view."""
        worlds = self.generator.get_available_worlds()
        
        # If we have a database controller, use it to get worlds
        if self.db_controller:
            try:
                db_worlds = self.db_controller.get_worlds()
                if db_worlds:
                    worlds = db_worlds
            except Exception as e:
                logger.error(f"Error loading worlds from database: {e}")
        
        self.view.set_worlds(worlds)
    
    def _handle_mission_generation(self, params: Dict[str, Any]):
        """
        Handle mission generation request from the view.
        
        Args:
            params: Dict with 'world', 'count', and 'use_gpt' keys
        """
        try:
            world = params["world"]
            count = params["count"]
            use_gpt = params["use_gpt"]
            
            # Generate missions
            self.missions = self.generator.generate_multiple_missions(
                world_data=world,
                count=count,
                use_gpt=use_gpt
            )
            
            # Update the view
            self.view.set_missions(self.missions)
            
        except Exception as e:
            logger.error(f"Error generating missions: {e}")
    
    def _handle_mission_save(self, mission: Dict[str, Any]):
        """
        Handle mission save request from the view.
        
        Args:
            mission: The mission dict to save
        """
        try:
            # If we have a database controller, save to database
            if self.db_controller:
                self.db_controller.save_mission(mission)
                logger.info(f"Saved mission '{mission['title']}' to database")
            else:
                logger.warning("No database controller available, mission not saved to database")
            
            # Update our local list
            for i, m in enumerate(self.missions):
                if m.get("id") == mission.get("id"):
                    self.missions[i] = mission
                    break
            
        except Exception as e:
            logger.error(f"Error saving mission: {e}")
    
    def get_widget(self) -> QWidget:
        """
        Get the view widget for embedding in the main UI.
        
        Returns:
            The mission generator view widget
        """
        return self.view
