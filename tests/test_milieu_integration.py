"""Integration test for milieu preference with sector controller."""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QListWidget, QTextEdit

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import controllers
from controller.settings_controller import SettingsController
from controller.sectors_controller import SectorController


class TestMilieuIntegration(unittest.TestCase):
    """Test integration of milieu preference with sector controller."""

    def setUp(self):
        """Set up test environment."""
        self.app = QApplication.instance() or QApplication([])
        self.settings = SettingsController()
        
        # Save original milieu setting to restore after test
        self.original_milieu = self.settings.load_milieu()
        
        # Create mock database
        self.mock_db = MagicMock()
        self.sectors_controller = SectorController(self.mock_db)
        
        # Setup test data
        self.test_sectors = [
            # sector_id, name, x, y, desc, img_path, abbrev, milieu
            (1, "Sector A", 0, 0, "Desc A", "path_a", "SA", "M1105"),
            (2, "Sector B", 1, 1, "Desc B", "path_b", "SB", "M1248"),
            (3, "Sector C", 2, 2, "Desc C", "path_c", "SC", "M1105"),
            (4, "Sector D", 3, 3, "Desc D", "path_d", "SD", "M990"),
        ]
        
        # Configure mock to return our test data
        self.mock_db.read_records.return_value = self.test_sectors

    def tearDown(self):
        """Clean up after tests."""
        # Restore original milieu setting
        self.settings.save_milieu(self.original_milieu)

    def test_get_sectors_by_milieu(self):
        """Test filtering sectors by milieu."""
        # Test filtering with M1105 milieu
        filtered_sectors = self.sectors_controller.get_sectors_by_milieu("M1105")
        self.assertEqual(len(filtered_sectors), 2)
        self.assertEqual(filtered_sectors[0][1], "Sector A")
        self.assertEqual(filtered_sectors[1][1], "Sector C")
        
        # Test filtering with M1248 milieu
        filtered_sectors = self.sectors_controller.get_sectors_by_milieu("M1248")
        self.assertEqual(len(filtered_sectors), 1)
        self.assertEqual(filtered_sectors[0][1], "Sector B")
        
        # Test filtering with M990 milieu
        filtered_sectors = self.sectors_controller.get_sectors_by_milieu("M990")
        self.assertEqual(len(filtered_sectors), 1)
        self.assertEqual(filtered_sectors[0][1], "Sector D")
        
        # Test filtering with non-existent milieu
        filtered_sectors = self.sectors_controller.get_sectors_by_milieu("M9999")
        self.assertEqual(len(filtered_sectors), 0)

    def test_load_sectors_with_milieu(self):
        """Test loading sectors with milieu filtering."""
        # Create mock widgets
        list_widget = QListWidget()
        details_widget = QTextEdit()
        
        # Set milieu preference
        self.settings.save_milieu("M1105")
        
        # Load sectors with default milieu (from settings)
        self.sectors_controller._load_sectors(list_widget, details_widget)
        
        # Verify only M1105 sectors were loaded
        self.assertEqual(list_widget.count(), 2)
        
        # Change milieu preference and reload
        self.settings.save_milieu("M1248")
        self.sectors_controller._load_sectors(list_widget, details_widget)
        
        # Verify only M1248 sectors were loaded
        self.assertEqual(list_widget.count(), 1)
        
        # Test explicit milieu parameter
        list_widget.clear()
        self.sectors_controller._load_sectors(list_widget, details_widget, milieu="M990")
        
        # Verify only M990 sectors were loaded
        self.assertEqual(list_widget.count(), 1)


if __name__ == '__main__':
    unittest.main()
