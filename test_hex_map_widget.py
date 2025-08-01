import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from view.hex_map_widget import HexMapWidget

class TestHexMapWidget(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.widget = HexMapWidget()
    
    def test_widget_creation(self):
        """Test that the widget is created successfully."""
        self.assertIsInstance(self.widget, HexMapWidget)
        self.assertEqual(self.widget.minimumWidth(), 600)
        self.assertEqual(self.widget.minimumHeight(), 400)
    
    def test_set_systems(self):
        """Test setting systems on the widget."""
        systems = [
            {"name": "Test System", "x": 1, "y": 1},
            {"name": "Another System", "x": 2, "y": 2}
        ]
        
        self.widget.set_systems(systems)
        self.assertEqual(len(self.widget.systems), 2)
        
    def test_pixel_to_hex_conversion(self):
        """Test pixel to hex coordinate conversion."""
        # Test basic conversion
        hex_coord = self.widget.pixel_to_hex(0, 0)
        self.assertIsInstance(hex_coord, tuple)
        self.assertEqual(len(hex_coord), 2)
        
    def test_find_system_at_hex(self):
        """Test finding a system at a hex coordinate."""
        systems = [
            {"name": "Test System", "x": 1, "y": 1},
            {"name": "Another System", "x": 2, "y": 2}
        ]
        
        self.widget.set_systems(systems)
        
        # Test finding a system
        system = self.widget._find_system_at_hex((1, 1))
        self.assertIsNotNone(system)
        self.assertEqual(system["name"], "Test System")
        
        # Test not finding a system
        system = self.widget._find_system_at_hex((5, 5))
        self.assertIsNone(system)
    
    def test_zoom_limits(self):
        """Test that zoom is limited to reasonable values."""
        # Test initial zoom
        self.assertEqual(self.widget.zoom_factor, 1.0)
        
        # Test min zoom limit
        self.widget.zoom_factor = self.widget.min_zoom - 0.1
        self.assertEqual(self.widget.zoom_factor, self.widget.min_zoom - 0.1)
        
        # Test max zoom limit
        self.widget.zoom_factor = self.widget.max_zoom + 0.1
        self.assertEqual(self.widget.zoom_factor, self.widget.max_zoom + 0.1)

if __name__ == '__main__':
    unittest.main()
