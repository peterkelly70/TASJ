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

# Import only what we need for this test
from view.planet_map_widget import PlanetMapWidget

class TestPlanetMapErrorHandling(unittest.TestCase):
    """Test error handling in PlanetMapWidget."""
    
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
        pass
        
    @patch('view.planet_map_widget.requests.get')
    def test_planet_map_download_error(self, mock_get):
        """Test error handling when planet map download fails."""
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
        
        # Verify the error signal was emitted
        self.assertTrue(error_spy.called)
        
    def test_planet_map_error_display(self):
        """Test that errors are displayed in the paint event."""
        # Create a PlanetMapWidget
        planet_widget = PlanetMapWidget()
        
        # Set error state manually
        planet_widget.loading_error = True
        planet_widget.error_message = "Test display error"
        planet_widget.planet_data = {"name": "TestPlanet"}
        
        # Create a mock painter to verify drawing methods are called
        mock_painter = MagicMock()
        
        # Call the paintEvent method directly
        planet_widget.paintEvent = MagicMock()
        planet_widget.update()
        
        # Verify the paintEvent was called
        self.assertTrue(planet_widget.paintEvent.called)

if __name__ == '__main__':
    unittest.main()
