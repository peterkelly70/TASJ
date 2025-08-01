import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import importlib

# Mock essential GUI parts minimally
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"--- TestAppInitialization: Added to sys.path: {project_root}")
print(f"--- TestAppInitialization: Current sys.path: {sys.path}")

# Attempt to preload the module to see if it resolves
try:
    print("--- TestAppInitialization: Attempting to import database.database_manager...")
    database_manager_module = importlib.import_module("database.database_manager")
    print(f"--- TestAppInitialization: Successfully imported {database_manager_module}")
except ImportError as e:
    print(f"--- TestAppInitialization: Failed to import database.database_manager directly: {e}")
    # Attempt to list contents of database directory
    try:
        db_dir_path = os.path.join(project_root, 'database')
        print(f"--- TestAppInitialization: Contents of {db_dir_path}: {os.listdir(db_dir_path)}")
    except Exception as list_e:
        print(f"--- TestAppInitialization: Could not list database directory: {list_e}")


# Now import the main application class *after* path adjustments
from main import HitchhikersGuideToTheGalaxy

class TestAppInitialization(unittest.TestCase):

    @patch('model.migrations.run_migrations') # Patch correct location
    @patch('model.traveller_database.TravellerDatabase') # Patch definition
    @patch('main.SettingsManager') # Keep this as it's likely needed early
    @patch('main.multiprocessing') # Mock multiprocessing entirely
    @patch('main.logging') # Mock logging
    def test_init_calls(self, mock_logging, mock_multiprocessing,
                      mock_settings, mock_db_class, mock_run_migrations):
        """Test initialization focuses on DB and migrations calls."""
        print("--- Running test_init_calls ---")

        # Setup mock return values
        mock_db_instance = MagicMock()
        mock_db_class.return_value = mock_db_instance
        mock_settings_instance = MagicMock()
        # Ensure settings return a db_type and db_path for the logic in main
        settings_dict = {
            'database_type': 'sqlite',
            'database_file_path': '/fake/path/to/db.sqlite'
        }
        mock_settings_instance.get_setting.side_effect = lambda key, default=None: settings_dict.get(key, default)
        mock_settings.return_value = mock_settings_instance

        # Mock QApplication sys.argv if needed by main execution flow
        with patch.object(sys, 'argv', ['main.py']):
             # Mock the QApplication class itself from QtWidgets
             with patch('PyQt6.QtWidgets.QApplication'):
                try:
                    print("--- Attempting HitchhikersGuideToTheGalaxy() init ---")
                    # Attempt to initialize the application
                    app = HitchhikersGuideToTheGalaxy()
                    print("--- HitchhikersGuideToTheGalaxy() init finished ---")

                    # Assertions
                    # Verify SettingsManager was used
                    mock_settings.assert_called_once()
                    # Verify migrations were called *correctly*
                    mock_run_migrations.assert_called_once_with('sqlite') # Expect only db_type
                    print("--- mock_run_migrations was called correctly ---")
                    # Verify DB was instantiated *correctly*
                    mock_db_class.assert_called_once_with(db_type='sqlite') # Expect db_type kwarg
                    print("--- mock_db_class was called correctly ---")
                    self.assertIsNotNone(app.db_instance, "app.db_instance should not be None")
                    self.assertEqual(app.db_instance, mock_db_instance, "app.db_instance should be the mocked instance")

                except Exception as e:
                    print(f"--- EXCEPTION during initialization: {e} ---")
                    import traceback
                    tb_str = traceback.format_exc()
                    self.fail(f"Initialization failed unexpectedly:\n{e}\n{tb_str}")

if __name__ == '__main__':
    print("--- Running test_initialization.py as main ---")
    unittest.main()
