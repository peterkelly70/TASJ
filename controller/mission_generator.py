"""
Mission Generator compatibility module.

This module provides backward compatibility for code that imports from controller.mission_generator.
It imports and re-exports the MissionGenerator class from the new modular structure.
"""

# Import and re-export the MissionGenerator class
from controller.mission_generator.mission_generator_base import MissionGenerator

# For backward compatibility, also import and re-export any utility functions
from controller.mission_generator.uwp_analyzer import uwp_summary
from controller.mission_generator.game_planner import GamePlannerTables

__all__ = ['MissionGenerator', 'uwp_summary', 'GamePlannerTables']
