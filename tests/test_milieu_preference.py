"""Tests for milieu preference functionality."""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only the settings controller to avoid circular imports
from controller.settings_controller import SettingsController


class TestMilieuPreference(unittest.TestCase):
    """Test cases for milieu preference functionality."""

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

    def test_save_load_milieu_preference(self):
        """Test saving and loading milieu preference."""
        test_milieu = "M1248"
        
        # Save milieu preference
        self.settings.save_milieu(test_milieu)
        
        # Load milieu preference
        loaded_milieu = self.settings.load_milieu()
        
        # Verify milieu was saved and loaded correctly
        self.assertEqual(loaded_milieu, test_milieu)
        
    def test_default_milieu(self):
        """Test default milieu value."""
        # Clear any existing milieu setting
        self.settings.settings.remove("milieu")
        
        # Load milieu preference with default
        loaded_milieu = self.settings.load_milieu()
        
        # Verify default milieu is returned
        self.assertEqual(loaded_milieu, "M1105")


if __name__ == '__main__':
    unittest.main()
