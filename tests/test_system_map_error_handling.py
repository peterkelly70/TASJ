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
from view.map_tabs_widget import SystemMapWidget

class TestSystemMapErrorHandling(unittest.TestCase):
    """Test error handling in SystemMapWidget."""
    
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
        
    def test_system_map_display_error(self):
        """Test that errors are displayed in the paint event."""
        # Create a SystemMapWidget with a mocked API
        system_widget = SystemMapWidget()
        
        # Set error state manually
        system_widget.loading_error = True
        system_widget.error_message = "Test display error"
        system_widget.system_data = {"name": "TestSystem"}
        
        # Create a mock painter to verify drawing methods are called
        mock_painter = MagicMock()
        
        # Call the error drawing method directly
        system_widget._draw_error_message(mock_painter)
        
        # Verify the painter was used to draw the error
        self.assertTrue(mock_painter.setPen.called)
        self.assertTrue(mock_painter.setFont.called)
        self.assertTrue(mock_painter.drawText.called)

if __name__ == '__main__':
    unittest.main()
