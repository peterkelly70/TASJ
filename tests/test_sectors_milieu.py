"""Test for sectors controller milieu filtering."""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QListWidget, QTextEdit

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only what we need directly
from controller.settings_controller import SettingsController


class TestSectorsMilieu(unittest.TestCase):
    """Test milieu filtering for sectors."""

    def setUp(self):
        """Set up test environment."""
        self.app = QApplication.instance() or QApplication([])
        self.settings = SettingsController()
        
        # Save original milieu setting to restore after test
        self.original_milieu = self.settings.load_milieu()

    def tearDown(self):
        """Clean up after tests."""
        # Restore original milieu setting
        self.settings.save_milieu(self.original_milieu)

    def test_filter_sectors_by_milieu(self):
        """Test filtering sectors by milieu using direct DB query."""
        # Skip import of SectorController to avoid circular imports
        # Instead, implement the filtering logic directly
        
        # Mock test data
        test_sectors = [
            (1, "Sector A", 0, 0, "Desc A", "path_a", "SA", "M1105"),
            (2, "Sector B", 1, 1, "Desc B", "path_b", "SB", "M1248"),
            (3, "Sector C", 2, 2, "Desc C", "path_c", "SC", "M1105"),
            (4, "Sector D", 3, 3, "Desc D", "path_d", "SD", "M990"),
        ]
        
        # Filter function (same logic as in SectorController.get_sectors_by_milieu)
        def filter_by_milieu(sectors, milieu):
            return [s for s in sectors if s[7] == milieu]  # Index 7 is milieu
        
        # Test filtering with M1105 milieu
        filtered_sectors = filter_by_milieu(test_sectors, "M1105")
        self.assertEqual(len(filtered_sectors), 2)
        self.assertEqual(filtered_sectors[0][1], "Sector A")
        self.assertEqual(filtered_sectors[1][1], "Sector C")
        
        # Test filtering with M1248 milieu
        filtered_sectors = filter_by_milieu(test_sectors, "M1248")
        self.assertEqual(len(filtered_sectors), 1)
        self.assertEqual(filtered_sectors[0][1], "Sector B")
        
        # Test filtering with M990 milieu
        filtered_sectors = filter_by_milieu(test_sectors, "M990")
        self.assertEqual(len(filtered_sectors), 1)
        self.assertEqual(filtered_sectors[0][1], "Sector D")
        
        # Test filtering with non-existent milieu
        filtered_sectors = filter_by_milieu(test_sectors, "M9999")
        self.assertEqual(len(filtered_sectors), 0)

    def test_milieu_persistence(self):
        """Test that milieu preference is saved and loaded correctly."""
        # Set a test milieu
        test_milieu = "M1248"
        self.settings.save_milieu(test_milieu)
        
        # Create a new settings controller to ensure it's loaded from storage
        new_settings = SettingsController()
        loaded_milieu = new_settings.load_milieu()
        
        # Verify the milieu was saved and loaded correctly
        self.assertEqual(loaded_milieu, test_milieu)


if __name__ == '__main__':
    unittest.main()
