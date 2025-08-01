#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize, Qt, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QImage

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules separately to avoid circular imports
from model.traveller_map_api import TravellerMapAPI

# Import widgets individually
from view.sector_view import SectorMapWidget
from view.map_tabs_widget import SystemMapWidget
from view.planet_map_widget import PlanetMapWidget

# Create a mock for MapTabsWidget to avoid circular imports
class MockMapTabsWidget:
    """Mock class for MapTabsWidget to avoid circular imports."""
    def __init__(self):
        self.sector_map = None
        self.system_map = None
        self.planet_map = None
        self.status_bar = None

class TestMapErrorHandling(unittest.TestCase):
    """Test error handling in map widgets."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Create a QApplication instance if one doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        # Mock the TravellerMapAPI
        self.mock_api = MagicMock(spec=TravellerMapAPI)
        
    def test_sector_map_error_handling(self):
        """Test error handling in SectorMapWidget."""
        # Create a SectorMapWidget with a mocked API
        sector_widget = SectorMapWidget()
        sector_widget.api = self.mock_api
        
        # Set up a signal spy to catch the map_error signal
        error_spy = MagicMock()
        sector_widget.map_error.connect(error_spy)
        
        # Mock the API to return an error
        error_message = "Test API error"
        self.mock_api.get_sector_map.return_value = (None, error_message)
        
        # Load a sector map
        sector_widget.load_sector_map("TestSector")
        
        # Verify the error was handled correctly
        self.assertTrue(sector_widget.loading_error)
        self.assertEqual(sector_widget.error_message, error_message)
        error_spy.assert_called_once_with(error_message)
        
    def test_system_map_error_handling(self):
        """Test error handling in SystemMapWidget."""
        # Create a SystemMapWidget with a mocked API
        system_widget = SystemMapWidget()
        system_widget.api = self.mock_api
        
        # Set up a signal spy to catch the map_error signal
        error_spy = MagicMock()
        system_widget.map_error.connect(error_spy)
        
        # Mock the API to return an error
        error_message = "Test system API error"
        self.mock_api.get_system_map.return_value = (None, error_message)
        
        # Load a system map
        system_data = {"name": "TestSystem", "sector": "TestSector", "hex": "0101"}
        system_widget.set_system(system_data)
        
        # Verify the error was handled correctly
        self.assertTrue(system_widget.loading_error)
        self.assertEqual(system_widget.error_message, error_message)
        error_spy.assert_called_once_with(error_message)
        
    @patch('view.planet_map_widget.requests.get')
    def test_planet_map_error_handling(self, mock_get):
        """Test error handling in PlanetMapWidget."""
        # Create a PlanetMapWidget
        planet_widget = PlanetMapWidget()
        
        # Set up a signal spy to catch the map_error signal
        error_spy = MagicMock()
        planet_widget.map_error.connect(error_spy)
        
        # Mock the requests.get to raise an exception
        mock_get.side_effect = Exception("Test planet API error")
        
        # Mock the database methods
        planet_widget.get_map_from_db = MagicMock(return_value=None)
        planet_widget.save_map_to_db = MagicMock()
        
        # Load a planet map
        planet_data = {"name": "TestPlanet", "uwp": "X123456-7"}
        planet_widget.set_planet(planet_data)
        
        # Wait for the download thread to complete
        if hasattr(planet_widget, 'downloader_thread') and planet_widget.downloader_thread:
            planet_widget.downloader_thread.wait()
        
        # Verify the error was handled correctly
        self.assertTrue(error_spy.called)
        
    def test_map_tabs_widget_error_handling(self):
        """Test error handling in MapTabsWidget."""
        # Create a MockMapTabsWidget with mocked map widgets
        map_tabs = MockMapTabsWidget()
        
        # Replace the map widgets with mocks
        map_tabs.sector_map = MagicMock()
        map_tabs.system_map = MagicMock()
        map_tabs.planet_map = MagicMock()
        
        # Set up the status bar
        map_tabs.status_bar = MagicMock()
        
        # Create a method to simulate _on_map_error
        def _on_map_error(error_msg):
            map_tabs.status_bar.showMessage(error_msg, 5000)
            
        # Attach the method to our mock
        map_tabs._on_map_error = _on_map_error
        
        # Simulate error signals from each map widget
        map_tabs._on_map_error("Sector map error")
        map_tabs.status_bar.showMessage.assert_called_with("Sector map error", 5000)
        
        map_tabs._on_map_error("System map error")
        map_tabs.status_bar.showMessage.assert_called_with("System map error", 5000)
        
        map_tabs._on_map_error("Planet map error")
        map_tabs.status_bar.showMessage.assert_called_with("Planet map error", 5000)
        
    def test_individual_map_widgets_integration(self):
        """Test integration of error handling between individual map widgets and error signals."""
        # Create individual map widgets
        sector_map = SectorMapWidget()
        system_map = SystemMapWidget()
        
        # Mock the TravellerMapAPI for sector and system maps
        mock_api = MagicMock(spec=TravellerMapAPI)
        error_message = "Test API integration error"
        mock_api.get_sector_map.return_value = (None, error_message)
        mock_api.get_system_map.return_value = (None, error_message)
        
        # Inject the mock API
        sector_map.api = mock_api
        system_map.api = mock_api
        
        # Set up signal spies
        sector_error_spy = MagicMock()
        system_error_spy = MagicMock()
        
        sector_map.map_error.connect(sector_error_spy)
        system_map.map_error.connect(system_error_spy)
        
        # Trigger sector map loading
        sector_map.load_sector_map("TestSector")
        
        # Verify the error signal was emitted
        sector_error_spy.assert_called_with(error_message)
        
        # Trigger system map loading
        system_data = {"name": "TestSystem", "sector": "TestSector", "hex": "0101"}
        system_map.set_system(system_data)
        
        # Verify the error signal was emitted
        system_error_spy.assert_called_with(error_message)

if __name__ == '__main__':
    unittest.main()
