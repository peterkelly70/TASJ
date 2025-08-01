"""
Tests for the mission generator functionality.

This module tests the mission generator controller, model, and integration.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import random
import logging

# Suppress warnings during tests
logging.basicConfig(level=logging.ERROR)

# Add the project root to the path so we can import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.mission_generator import MissionGenerator
from controller.mission_generator.uwp_analyzer import uwp_summary
from controller.mission_generator.game_planner import GamePlannerTables


class TestMissionGenerator(unittest.TestCase):
    """Test cases for the MissionGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the OpenAI API key check
        with patch('os.getenv', return_value=None):
            self.generator = MissionGenerator()
        
        # Provide test data
        self.generator.worlds = [
            {
                "name": "TestWorld",
                "UWP": "A553A85-D",
                "remarks": "Hi In Cp",
                "zone": "",
                "bases": "NS",
                "stellar": "M2 V",
                "trade_codes": ["High Pop", "Industrial", "Capital"]
            }
        ]
        
        # Set a fixed seed for reproducibility
        random.seed(42)
    
    def test_uwp_summary(self):
        """Test the UWP summary function."""
        # Use the imported uwp_summary function directly
        summary = uwp_summary("A553A85-D")
        # The population code 'A' corresponds to 'teeming megacities' in the generator
        self.assertIn("teeming megacities", summary)
        self.assertIn("class A starport", summary)
        self.assertIn("TL-D", summary)
    
    def test_load_game_planner_tables(self):
        """Test loading the game planner tables."""
        # Create a GamePlannerTables instance with mocked _parse_game_planner_file
        game_planner = GamePlannerTables()
        
        # Mock the file parsing method to return test data
        mock_tables = {
            "PHASE 1": {
                "1": {
                    "name": "General Type of Scenario",
                    "entries": {
                        "1": {"name": "Investigation", "reference": "2"},
                        "2": {"name": "Exploration", "reference": "3"}
                    }
                }
            }
        }
        
        with patch.object(game_planner, '_parse_game_planner_file', return_value=mock_tables):
            tables = game_planner.load_tables()
        
        # Verify we have tables
        self.assertIsInstance(tables, dict)
        
        # Check for expected phases
        self.assertIn("PHASE 1", tables)
        
        # Check for expected tables in Phase 1
        self.assertIn("1", tables["PHASE 1"])
        
        # Check for scenario types in table 1
        self.assertEqual(tables["PHASE 1"]["1"]["name"], "General Type of Scenario")
        self.assertIn("entries", tables["PHASE 1"]["1"])
    
    def test_roll_on_table(self):
        """Test rolling on a game planner table."""
        # Create a GamePlannerTables instance with mock tables
        game_planner = GamePlannerTables()
        game_planner.tables = {
            "PHASE 1": {
                "1": {
                    "name": "Test Table",
                    "entries": {
                        "1": {"name": "Test Entry 1", "reference": "2"},
                        "2": {"name": "Test Entry 2", "reference": None}
                    }
                }
            }
        }
        
        # Test rolling on a valid table
        with patch('random.choice', return_value="1"):
            name, entry_id, reference = game_planner.roll_on_table("PHASE 1", "1")
            self.assertEqual(name, "Test Entry 1")
            self.assertEqual(entry_id, "1")
            self.assertEqual(reference, "2")
        
        # Test rolling on an invalid table
        name, entry_id, reference = game_planner.roll_on_table("INVALID", "999")
        self.assertEqual(name, "Unknown")
        self.assertEqual(entry_id, "0")
        self.assertIsNone(reference)
    
    def test_generate_mission_structure(self):
        """Test generating a mission structure."""
        # Mock the game_planner with a complete structure
        mock_game_planner = MagicMock()
        mock_game_planner.roll_on_table.side_effect = [
            ("Investigation", "1", "2"),  # Scenario type with reference to table 2
            ("Where are they", "1", "4"),  # Detail 1 with reference to table 4
            ("Alien structure", "1", None)  # Detail 2 with no further reference
        ]
        mock_game_planner.get_table_info.return_value = {"name": "Test Table"}
        
        # Replace the generator's game_planner with our mock
        self.generator.game_planner = mock_game_planner
        
        # Generate mission structure
        mission = self.generator.generate_mission_structure()
        
        # Check mission structure
        self.assertEqual(mission.scenario_type["name"], "Investigation")
        
        # Check details
        self.assertIsNotNone(mission.details)
        self.assertGreaterEqual(len(mission.details), 1)
        
        # Check references
        self.assertIsNotNone(mission.references)
        self.assertGreaterEqual(len(mission.references), 1)
    
    def test_generate_mission_for_world(self):
        """Test generating a complete mission for a world."""
        # Mock the generate_mission_structure method
        with patch.object(self.generator, 'generate_mission_structure') as mock_structure:
            from model.mission import Mission, MissionParticulars
            mock_mission = Mission(
                world={},
                scenario_type={"name": "Investigation", "id": "1"},
                particulars=MissionParticulars(content="Test content")
            )
            # Create details in the format expected by _generate_basic_particulars
            mock_mission.details = {
                "Type of Investigation": {"name": "Where are they", "id": "1"},
                "Type of Exploration": {"name": "Alien structure", "id": "1"}
            }
            mock_mission.references = []
            mock_structure.return_value = mock_mission
            
            # Mock the _generate_map_description method
            with patch.object(self.generator, '_generate_map_description') as mock_map:
                mock_map.return_value = "Test map description"
                
                # Mock the particulars generation
                with patch('controller.mission_generator.mission_particulars.generate_mission_particulars') as mock_particulars:
                    mock_particulars.return_value = MissionParticulars(content="Test particulars")
                    
                    # Mock the db_manager
                    self.generator.db_manager = MagicMock()
                    self.generator.db_manager.save_mission.return_value = mock_mission
                    
                    # Generate a mission
                    world_data = self.generator.worlds[0]
                    mission = self.generator.generate_mission_for_world(world_data, use_gpt=False)
                    
                    # Check mission
                    self.assertEqual(mission.world, world_data)
                    self.assertEqual(mission.map_description, "Test map description")
    
    def test_generate_multiple_missions(self):
        """Test generating multiple missions."""
        # Mock the generate_mission_for_world method
        with patch.object(self.generator, 'generate_mission_for_world') as mock_generate:
            from model.mission import Mission
            mock_mission = Mission(world={}, scenario_type={"name": "Test Mission"})
            mock_generate.return_value = mock_mission
            
            # Generate multiple missions
            world_data = self.generator.worlds[0]
            missions = self.generator.generate_multiple_missions(world_data, count=3, use_gpt=False)
            
            # Check missions
            self.assertEqual(len(missions), 3)
            for mission in missions:
                self.assertEqual(mission.scenario_type["name"], "Test Mission")
            
            # Verify the method was called the correct number of times
            self.assertEqual(mock_generate.call_count, 3)


if __name__ == '__main__':
    unittest.main()
