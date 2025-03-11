# Example for characters_controller.py

class CharactersController:
    def __init__(self, db_instance):
        self.db = db_instance

    def show_view(self, display_widget):
        display_widget.setText("Characters button has been pushed")
        # Interact with the database if needed
        # characters = self.db.query_characters()  # Example placeholder method
        # character_names = [character[1] for character in characters]  # Assuming name is the second field
        # display_widget.append("\n".join(character_names))
