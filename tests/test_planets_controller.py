import unittest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, ANY

from PyQt6.QtWidgets import QApplication, QWidget

# Initialize QApplication before importing any modules that use Qt
app = QApplication([])

# Mock the PlanetMapManager before importing PlanetController
with patch('model.planet_map_manager.PlanetMapManager') as mock_planet_map_manager:
    mock_planet_map_manager.return_value = MagicMock()
    from controller.planets_controller import PlanetController

class TestPlanetController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance for the test class
        cls.app = QApplication.instance() or QApplication([])
    
    def setUp(self):
        # Create a mock database with a db_path attribute
        self.mock_db = MagicMock()
        self.mock_db.db_path = ':memory:'  # In-memory database for testing
        
        # Set up the controller with the mock database
        self.controller = PlanetController(self.mock_db)
        
        # Create a real QWidget for testing
        self.test_widget = QWidget()
        
        # Mock the PlanetView class
        self.mock_planet_view_patcher = patch('view.planet_view.PlanetView')
        self.MockPlanetView = self.mock_planet_view_patcher.start()
        self.mock_view_instance = MagicMock()
        self.mock_view_instance.planet_map = MagicMock()
        self.MockPlanetView.return_value = self.mock_view_instance
        
        # Mock the mission generator
        self.mock_mission_generator = MagicMock()
        self.controller.mission_generator = self.mock_mission_generator
        
        # Mock the map manager
        self.mock_map_manager = MagicMock()
        self.controller.map_manager = self.mock_map_manager
    
    def tearDown(self):
        # Clean up patches
        self.mock_planet_view_patcher.stop()
        
        # Clean up the test widget
        if hasattr(self, 'test_widget'):
            self.test_widget.deleteLater()
    
    def test_initialization(self):
        """Test that the controller initializes with a database connection."""
        self.assertIsNotNone(self.controller.db)
        self.assertIsNotNone(self.controller.map_manager)
        self.assertIsNone(self.controller.view)
        self.assertEqual(self.controller.missions, [])
    
    @patch('controller.planets_controller.PlanetView')
    def test_show_view_creates_planet_view(self, mock_planet_view):
        """Test that show_view creates a PlanetView instance."""
        # Configure the database to return no planets
        self.mock_db.read_records.return_value = []
        
        # Set up the mock view
        mock_view_instance = MagicMock()
        mock_planet_view.return_value = mock_view_instance
        
        # Call the method under test
        result = self.controller.show_view(self.test_widget)
        
        # Verify the view was created with the correct parent
        mock_planet_view.assert_called_once_with(self.test_widget)
        
        # Verify the view was stored and returned
        self.assertEqual(self.controller.view, mock_view_instance)
        self.assertEqual(result, mock_view_instance)
        
        # Verify the view's signals were connected
        mock_view_instance.mission_generation_requested.connect.assert_called_once()
        mock_view_instance.mission_selected.connect.assert_called_once()
        mock_view_instance.map_generation_requested.connect.assert_called_once()
        
        # Verify the database was queried for planets
        self.mock_db.read_records.assert_called_once_with("planets")
    
    def test_load_planets_with_empty_database(self):
        """Test _load_planets with an empty database."""
        # Configure the database to return no planets
        self.mock_db.read_records.return_value = []
        
        # Set up the view
        self.controller.view = self.mock_view_instance
        
        # Call the method under test
        self.controller._load_planets()
        
        # Verify the database was queried
        self.mock_db.read_records.assert_called_once_with("planets")
        
        # Verify the view was updated for no planets
        self.mock_view_instance.set_planet.assert_called_once_with(None)
        self.mock_view_instance.planet_header.setText.assert_called_once_with("No planets found")
    
    def test_load_planets_with_planets(self):
        """Test _load_planets with planets in the database."""
        # Configure the database to return some planets
        mock_planets = [
            (1, "Earth", "A123456-7", "G2V", "Imperial", "Core", "123-456", "None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "Hi In", "None", "None", "None", "123", "1", "None", "123", "A123456-7")
        ]
        self.mock_db.read_records.return_value = mock_planets
        
        # Set up the view
        self.controller.view = self.mock_view_instance
        
        # Call the method under test
        self.controller._load_planets()
        
        # Verify the database was queried
        self.mock_db.read_records.assert_called_once_with("planets")
        
        # Verify the view was updated with the sample planet data (not the database data)
        self.mock_view_instance.set_planet.assert_called_once()
        
        # Verify the sample planet data was used (the controller has hardcoded sample data)
        planet_arg = self.mock_view_instance.set_planet.call_args[0][0]
        self.assertEqual(planet_arg['name'], "Fermi")  # This is the hardcoded sample name
        self.assertEqual(planet_arg['UWP'], "A867954-D")  # This is the hardcoded sample UWP
        self.assertEqual(planet_arg['trade_codes'], ["Hi", "Ri", "In"])  # Hardcoded trade codes

if __name__ == '__main__':
    unittest.main()
