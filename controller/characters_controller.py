# Example for characters_controller.py

class CharactersController:
    def __init__(self, db_instance):
        """Initialize the characters controller with a database instance."""
        self.db = db_instance

    def show_view(self, display_widget):
        """Display characters in the widget.
        
        Args:
            display_widget: The widget to display characters in
        """
        # Clear any existing text
        display_widget.setText("")
        
        # Query characters from database
        characters = self.db.query_characters()
        
        # If no characters, return without appending
        if not characters:
            return
            
        # Format and display character names
        character_names = [character[1] for character in characters]
        display_widget.append("\n".join(character_names))

    def query_characters(self):
        """Query characters from the database.
        
        Returns:
            list: List of tuples containing character data
        """
        return self.db.query_characters()

    def add_character(self, character_data):
        """Add a new character to the database.
        
        Args:
            character_data: Dictionary containing character information
        """
        self.db.add_character(character_data)

    def update_character(self, character_id, character_data):
        """Update an existing character in the database.
        
        Args:
            character_id: ID of the character to update
            character_data: Dictionary containing updated character information
        """
        self.db.update_character(character_id, character_data)

    def delete_character(self, character_id):
        """Delete a character from the database.
        
        Args:
            character_id: ID of the character to delete
        """
        self.db.delete_character(character_id)
