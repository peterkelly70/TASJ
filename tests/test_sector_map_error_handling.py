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
from model.traveller_map_api import TravellerMapAPI
from view.sector_view import SectorMapWidget

class TestSectorMapErrorHandling(unittest.TestCase):
    """Test error handling in SectorMapWidget."""
    
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

if __name__ == '__main__':
    unittest.main()
