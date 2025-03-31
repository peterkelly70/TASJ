import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os
import logging
from main import HitchhikersGuideToTheGalaxy, SettingsDialog, UISettings
from utils.flow_layout import FlowLayout

class TestHitchhikersGuideToTheGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a QApplication for the tests
        cls.app = QApplication([])
        # Configure test logging
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(__name__)

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary config for testing
        self.test_config = {
            'theme': 'Light',
            'font_family': 'Arial',
            'font_size': 10
        }
        self.window = HitchhikersGuideToTheGalaxy()

    def test_initial_state(self):
        """Test initial application state."""
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), "Hitchhiker's Guide to the Galaxy")
        self.assertTrue(hasattr(self.window, 'db_instance'))
        self.assertTrue(hasattr(self.window, 'data_download_controller'))

    def test_theme_switching(self):
        """Test theme switching functionality."""
        # Test light theme
        self.window.current_theme = "Light"
        self.window.apply_theme_and_font()
        self.assertIn("background-color: white", self.window.styleSheet())

        # Test dark theme
        self.window.current_theme = "Dark"
        self.window.apply_theme_and_font()
        self.assertIn("background-color: #2e2e2e", self.window.styleSheet())

    def test_font_settings(self):
        """Test font customization."""
        test_font = QFont("Times New Roman", 12)
        self.window.current_font = test_font
        self.window.apply_theme_and_font()
        self.assertEqual(self.window.font().family(), "Times New Roman")
        self.assertEqual(self.window.font().pointSize(), 12)

    @patch('main.QFontDialog.getFont')
    def test_settings_dialog(self, mock_get_font):
        """Test settings dialog functionality."""
        # Mock font dialog return value
        mock_font = QFont("Arial", 11)
        mock_get_font.return_value = (mock_font, True)

        # Create settings dialog
        dialog = SettingsDialog("Light", QFont("Arial", 10), self.window)
        
        # Test theme selection
        dialog.theme_combo.setCurrentText("Dark")
        self.assertEqual(dialog.theme_combo.currentText(), "Dark")

        # Test font selection
        dialog.choose_font()
        self.assertEqual(dialog.selected_font, mock_font)

    def test_database_initialization(self):
        """Test database initialization."""
        self.assertIsNotNone(self.window.db_instance)
        self.assertEqual(self.window.db_instance.db_type, os.getenv("DATABASE_TYPE", "sqlite"))

    @patch('main.DataDownloadController.start_download')
    def test_download_functionality(self, mock_start_download):
        """Test data download functionality."""
        self.window.download_all_data()
        mock_start_download.assert_called_once()
        self.assertTrue(self.window.cancel_button.isEnabled())

    def test_error_handling(self):
        """Test error handling in main operations."""
        # Test invalid database type
        with self.assertRaises(ValueError):
            with patch.dict(os.environ, {'DATABASE_TYPE': 'invalid_type'}):
                HitchhikersGuideToTheGalaxy()

    # Original button tests
    def test_sector_button(self):
        self.window.sector_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_planet_button(self):
        self.window.planet_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_people_button(self):
        self.window.people_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_lifeforms_button(self):
        self.window.lifeforms_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_ships_button(self):
        self.window.ships_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_vehicals_button(self):
        self.window.vehicle_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_events_button(self):
        self.window.events_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_technology_button(self):
        self.window.technology_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_organizations_button(self):
        self.window.organizations_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_adventure_hooks_button(self):
        self.window.adventure_hooks_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "")

    def test_progress_monitoring(self):
        """Test progress monitoring functionality."""
        # Test progress update
        self.window.progress_queue.put("Progress: 50")
        self.window.update_progress()
        self.assertEqual(self.window.progress_bar.value(), 50)

        # Test completion
        self.window.progress_queue.put("Download complete!")
        self.window.update_progress()
        self.assertEqual(self.window.progress_bar.value(), 100)
        self.assertFalse(self.window.cancel_button.isEnabled())

    def test_button_layout(self):
        """Test that buttons are properly added to flow layout."""
        # Get the button container
        central_widget = self.window.centralWidget()
        main_layout = central_widget.layout()
        top_layout = main_layout.itemAt(0).layout()
        button_container = top_layout.itemAt(0).widget()
        flow_layout = button_container.layout()
        
        # Verify flow layout is used
        self.assertIsInstance(flow_layout, FlowLayout)
        
        # Verify buttons are added
        button_count = flow_layout.count()
        expected_buttons = [
            "Sectors", "Planets", "Characters",
            "Lifeforms", "Ships", "Vehicle",
            "Events", "Technology", "Organizations",
            "Adventure Hooks"
        ]
        self.assertEqual(button_count, len(expected_buttons))

    def test_button_wrap(self):
        """Test that buttons wrap when window is resized."""
        # Get the button container
        central_widget = self.window.centralWidget()
        main_layout = central_widget.layout()
        top_layout = main_layout.itemAt(0).layout()
        button_container = top_layout.itemAt(0).widget()
        flow_layout = button_container.layout()
        
        # Get initial button positions
        initial_positions = []
        for i in range(flow_layout.count()):
            item = flow_layout.itemAt(i)
            widget = item.widget()
            initial_positions.append(widget.pos())
            
        # Resize window to force wrapping
        self.window.resize(400, 800)
        
        # Get new positions
        new_positions = []
        for i in range(flow_layout.count()):
            item = flow_layout.itemAt(i)
            widget = item.widget()
            new_positions.append(widget.pos())
            
        # Verify positions have changed
        self.assertNotEqual(initial_positions, new_positions)

    def tearDown(self):
        """Clean up after each test."""
        self.window.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.app.quit()

if __name__ == "__main__":
    unittest.main()
