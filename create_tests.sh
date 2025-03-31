#!/bin/bash

# Create test files
cd /home/peter/Projects/TASJ/tests
touch test_characters_controller.py
touch test_planets_controller.py
touch test_sectors_controller.py
touch test_organizations_controller.py
touch test_lifeforms_controller.py
touch test_ships_controller.py
touch test_technology_controller.py
touch test_theme_controller.py
touch test_settings_controller.py
touch test_adventure_hooks_controller.py
touch test_adventure_planner.py

# Add content to each file
echo "import unittest
from unittest.mock import Mock, patch
from controller.characters_controller import CharactersController

class TestCharactersController(unittest.TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.controller = CharactersController(self.mock_db)
        self.mock_widget = Mock()

    def test_initialization(self):
        self.assertIsNotNone(self.controller.db)

    def test_show_view_sets_text(self):
        expected_text = \"Characters button has been pushed\"
        self.controller.show_view(self.mock_widget)
        self.mock_widget.setText.assert_called_once_with(expected_text)

    def test_show_view_handles_empty_database(self):
        self.mock_db.query_characters.return_value = []
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_characters.assert_called_once()
        self.mock_widget.append.assert_not_called()

    def test_show_view_handles_multiple_characters(self):
        mock_characters = [
            (\"char1\", \"John\"),
            (\"char2\", \"Jane\")
        ]
        self.mock_db.query_characters.return_value = mock_characters
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_characters.assert_called_once()
        self.mock_widget.append.assert_called_once_with(\"\\n\".join([\"John\", \"Jane\"]))" > test_characters_controller.py

echo "import unittest
from unittest.mock import Mock, patch
from controller.planets_controller import PlanetController

class TestPlanetController(unittest.TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.controller = PlanetController(self.mock_db)
        self.mock_widget = Mock()

    def test_initialization(self):
        self.assertIsNotNone(self.controller.db)

    def test_show_view_sets_text(self):
        expected_text = \"Planet button has been pushed\"
        self.controller.show_view(self.mock_widget)
        self.mock_widget.setText.assert_called_once_with(expected_text)

    def test_show_view_handles_empty_database(self):
        self.mock_db.query_planets.return_value = []
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_planets.assert_called_once()
        self.mock_widget.append.assert_not_called()

    def test_show_view_handles_multiple_planets(self):
        mock_planets = [
            (\"planet1\", \"Earth\"),
            (\"planet2\", \"Mars\")
        ]
        self.mock_db.query_planets.return_value = mock_planets
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_planets.assert_called_once()
        self.mock_widget.append.assert_called_once_with(\"\\n\".join([\"Earth\", \"Mars\"]))" > test_planets_controller.py

# Add similar content for other test files...

echo "if __name__ == '__main__':
    unittest.main()" >> test_characters_controller.py
echo "if __name__ == '__main__':
    unittest.main()" >> test_planets_controller.py
# Add similar if __name__ == '__main__' block to other test files
