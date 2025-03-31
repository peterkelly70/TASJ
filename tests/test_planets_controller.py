import unittest
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
        expected_text = "Planet button has been pushed"
        self.controller.show_view(self.mock_widget)
        self.mock_widget.setText.assert_called_once_with(expected_text)

    def test_show_view_handles_empty_database(self):
        self.mock_db.query_planets.return_value = []
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_planets.assert_called_once()
        self.mock_widget.append.assert_not_called()

    def test_show_view_handles_multiple_planets(self):
        mock_planets = [
            ("planet1", "Earth"),
            ("planet2", "Mars")
        ]
        self.mock_db.query_planets.return_value = mock_planets
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_planets.assert_called_once()
        self.mock_widget.append.assert_called_once_with("\n".join(["Earth", "Mars"]))
if __name__ == '__main__':
    unittest.main()
