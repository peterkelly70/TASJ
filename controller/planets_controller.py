# In controller/planets_controller.py

class PlanetController:
    def __init__(self, db_instance):
        self.db = db_instance

    def show_view(self, display_widget):
        display_widget.setText("Planet button has been pushed")

        # Example of using the database instance (this is just a placeholder):
        # planets = self.db.query_planets()  # Assuming query_planets() exists and returns a list of planets
        # planet_names = [planet[1] for planet in planets]  # Assuming the planet name is the second field
        # display_widget.append("\n".join(planet_names))
