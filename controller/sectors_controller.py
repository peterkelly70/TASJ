class SectorController:
    def __init__(self, db_instance):
        self.db = db_instance

    def show_view(self, display_widget):
        # You can now use self.db to interact with the database if needed
        display_widget.setText("Sector button has been pushed")

        # Example of interacting with the database (this is just a placeholder):
        # sectors = self.db.query_sectors()
        # sector_names = [sector[1] for sector in sectors]  # Assuming sector name is the second field
        # display_widget.append("\n".join(sector_names))