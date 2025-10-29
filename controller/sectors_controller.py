from model.sectors_db import SectorDB
from model.planets_db import PlanetDB
from utils.map_renderer import (
    generate_planet_hex_map,
    render_planet_hex_map_hexes,
    render_sector_from_api,
    generate_system_map,
)
from view.sector_view import SectorView
from PyQt6.QtCore import Qt

class SectorController:
    def __init__(self, db_instance):
        self.sector_model = SectorDB(db_instance)
        self.planet_model = PlanetDB(db_instance)
        self.sector_view = None
        self.selected_sector_id = None
        self.current_sector_name = None
        self.current_planet_details = None

    def _ensure_view(self):
        if not self.sector_view:
            self.sector_view = SectorView()

            # Connect signals and slots for interactivity
            self.sector_view.sectors_list.itemClicked.connect(self.on_sector_selected)
            self.sector_view.systems_list.itemClicked.connect(self.on_system_selected)
            self.sector_view.planets_list.itemClicked.connect(self.on_planet_selected)
            self.sector_view.sector_search_input.textChanged.connect(self.filter_sectors)
            self.sector_view.system_search_input.textChanged.connect(self.filter_systems)
            self.sector_view.generate_sector_button.clicked.connect(self.generate_sector_map)
            self.sector_view.generate_planet_button.clicked.connect(self.generate_planet_map)
            self.sector_view.generate_galaxy_button.clicked.connect(self.generate_galaxy_map)

            # Load initial data
            self.load_sectors()

        return self.sector_view

    def show_view(self, display_widget=None):
        """Prepare the Galaxy view and optionally attach it to a widget container."""
        view = self._ensure_view()

        if display_widget is not None:
            if hasattr(display_widget, "setWidget"):
                display_widget.setWidget(view)
            elif hasattr(display_widget, "append"):
                display_widget.append("Galaxy view is available in widget mode.")

        return view
    
    def load_sectors(self):
        """Load sectors from the database into the view."""
        if not self.sector_view:
            return

        try:
            sectors = self.sector_model.list_sector_names()

            # Clear and populate the list
            self.sector_view.sectors_list.clear()
            for sector_name in sectors:
                self.sector_view.sectors_list.addItem(sector_name)
        except Exception as e:
            print(f"Error loading sectors: {e}")
    
    def on_sector_selected(self, item):
        """Handle sector selection."""
        sector_name = item.text()
        sector_record = self.sector_model.get_sector_by_name(sector_name)
        if not sector_record:
            self.selected_sector_id = None
            self.sector_view.systems_list.clear()
            self.sector_view.planets_list.clear()
            self.sector_view.sector_info_content.setText(f"Sector not found: {sector_name}")
            return

        self.selected_sector_id = sector_record[0]
        self.current_sector_name = sector_name
        self.sector_view.sector_info_content.setText(f"Selected sector: {sector_name}")
        self.current_planet_details = None
        self.sector_view.generate_planet_button.setEnabled(False)
        self.sector_view.planet_map_label.setText("Select a planet and generate a map")

        # Load systems for this sector
        self.load_systems_for_sector(self.selected_sector_id)
    
    def load_systems_for_sector(self, sector_id):
        """Load systems for the selected sector."""
        try:
            systems = self.sector_model.list_systems_by_sector(sector_id)

            # Clear and populate the list
            self.sector_view.systems_list.clear()
            self.sector_view.planets_list.clear()
            for hex_code, name in systems:
                label = f"{hex_code} - {name}" if name else hex_code
                self.sector_view.systems_list.addItem(label)
        except Exception as e:
            print(f"Error loading systems: {e}")
    
    def on_system_selected(self, item):
        """Handle system selection."""
        system_label = item.text()
        system_hex = system_label.split(' - ', 1)[0].strip()
        # Update system info panel
        self.sector_view.system_info_content.setText(f"Selected system: {system_label}")
        
        # Load planets for this system
        self.load_planets_for_system(system_hex)
    
    def load_planets_for_system(self, system_hex):
        """Load planets for the selected system."""
        if self.selected_sector_id is None:
            return
        try:
            planets = self.planet_model.list_planets_by_system(self.selected_sector_id, system_hex)

            # Clear and populate the list
            self.sector_view.planets_list.clear()
            for planet_name in planets:
                self.sector_view.planets_list.addItem(planet_name)
            self.current_planet_details = None
            self.sector_view.generate_planet_button.setEnabled(False)
        except Exception as e:
            print(f"Error loading planets: {e}")

    def on_planet_selected(self, item):
        """Handle planet selection."""
        planet_name = item.text()
        # Update planet info panel
        self.sector_view.planet_info_content.setText(f"Selected planet: {planet_name}")
        self.current_planet_details = self.planet_model.get_planet_details(planet_name, self.selected_sector_id)
        self.sector_view.generate_planet_button.setEnabled(self.current_planet_details is not None)

    def filter_sectors(self, text):
        """Filter sectors list based on search text."""
        for i in range(self.sector_view.sectors_list.count()):
            item = self.sector_view.sectors_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def filter_systems(self, text):
        """Filter systems list based on search text."""
        for i in range(self.sector_view.systems_list.count()):
            item = self.sector_view.systems_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    # ------------------------------------------------------------------
    # Map generation
    # ------------------------------------------------------------------

    def generate_sector_map(self):
        if self.selected_sector_id is None or not self.current_sector_name:
            return
        pixmap = render_sector_from_api(self.current_sector_name)

        if pixmap is None:
            self.sector_view.sector_map_label.setText("Unable to download sector map.")
        else:
            self.sector_view.map_tabs.setCurrentWidget(self.sector_view.sector_map_tab)
            self.sector_view.sector_map_label.setPixmap(pixmap)

    def generate_planet_map(self):
        if not self.current_planet_details:
            return
        try:
            hex_map = generate_planet_hex_map(self.current_planet_details)
            pixmap = render_planet_hex_map_hexes(hex_map)
            self.sector_view.map_tabs.setCurrentWidget(self.sector_view.planet_map_tab)
            self.sector_view.planet_map_label.setPixmap(pixmap)
        except ValueError as exc:
            self.sector_view.planet_map_label.setText(str(exc))

    def generate_galaxy_map(self):
        if not self.current_planet_details:
            self.sector_view.galaxy_map_label.setText("Select a planet to render the system")
            return

        system_name = self.current_planet_details.get("system_name") or self.current_sector_name or "System"
        pixmap = generate_system_map(system_name, self.current_planet_details)
        self.sector_view.map_tabs.setCurrentWidget(self.sector_view.galaxy_map_tab)
        self.sector_view.galaxy_map_label.setPixmap(pixmap)
