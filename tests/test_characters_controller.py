import unittest
from unittest.mock import Mock, patch
from controller.characters_controller import CharactersController

class TestCharactersController(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.controller = CharactersController(self.mock_db)
        self.mock_widget = Mock()

    def test_initialization(self):
        """Test that the controller initializes with a database instance."""
        self.assertIsNotNone(self.controller.db)

    def test_show_view_sets_text(self):
        """Test that show_view clears and sets text in the widget."""
        self.mock_db.query_characters.return_value = []
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_characters.assert_called_once()
        self.mock_widget.setText.assert_called_once_with("")
        self.mock_widget.append.assert_not_called()

    def test_show_view_handles_empty_database(self):
        """Test that show_view handles an empty database."""
        self.mock_db.query_characters.return_value = []
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_characters.assert_called_once()
        self.mock_widget.setText.assert_called_once_with("")
        self.mock_widget.append.assert_not_called()

    def test_show_view_handles_multiple_characters(self):
        """Test that show_view handles multiple characters."""
        mock_characters = [
            ("char1", "John"),
            ("char2", "Jane")
        ]
        self.mock_db.query_characters.return_value = mock_characters
        self.controller.show_view(self.mock_widget)
        self.mock_db.query_characters.assert_called_once()
        self.mock_widget.append.assert_called_once_with("John\nJane")

    def test_query_characters(self):
        """Test that query_characters delegates to the database."""
        mock_result = [("char1", "John")]
        self.mock_db.query_characters.return_value = mock_result
        result = self.controller.query_characters()
        self.assertEqual(result, mock_result)

    def test_add_character(self):
        """Test that add_character delegates to the database."""
        mock_data = {"name": "John"}
        self.controller.add_character(mock_data)
        self.mock_db.add_character.assert_called_once_with(mock_data)

    def test_update_character(self):
        """Test that update_character delegates to the database."""
        mock_id = "char1"
        mock_data = {"name": "John"}
        self.controller.update_character(mock_id, mock_data)
        self.mock_db.update_character.assert_called_once_with(mock_id, mock_data)

    def test_delete_character(self):
        """Test that delete_character delegates to the database."""
        mock_id = "char1"
        self.controller.delete_character(mock_id)
        self.mock_db.delete_character.assert_called_once_with(mock_id)

if __name__ == '__main__':
    unittest.main()
