import logging
import os
from PyQt6.QtWidgets import (QTextEdit, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QWidget, QSplitter, QLabel, QLineEdit, QHBoxLayout, 
                             QGraphicsView, QGraphicsScene, QFrame, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QFont, QPen, QBrush, QColor
from view.sector_view import SectorView
from model.sectors_db import SectorDB

# Style constants
FONT_FAMILY = "Courier New"
TEXT_COLOR = "#00FF00"
HIGHLIGHT_COLOR = "#AAFFAA"
HEADER_STYLE = f"color: {TEXT_COLOR}; font-weight: bold;"
TERMINAL_STYLE = f"background-color: #0A0A0A; color: {TEXT_COLOR}; font-family: {FONT_FAMILY};"
MAP_PLACEHOLDER_STYLE = "background-color: #222; color: #ddd; border: 1px solid #444;"
DETAILS_DIV_STYLE = f"font-family: {FONT_FAMILY}; color: {TEXT_COLOR};"
TABLE_STYLE = "width: 100%; border-collapse: collapse;"
TABLE_HEADER_STYLE = f"color: {HIGHLIGHT_COLOR};"
TABLE_CELL_STYLE = f"padding: 5px; color: {HIGHLIGHT_COLOR};"
SECTION_HEADER_STYLE = f"color: {HIGHLIGHT_COLOR};"
SEPARATOR_STYLE = "border-color: #004400;"

logger = logging.getLogger(__name__)

class SectorController(QObject):
    # Signal emitted when a sector is selected, passing the sector data
    sector_changed = pyqtSignal(dict)
    
    def __init__(self, db_instance):
        super().__init__()
        self.db = db_instance
        self.sectors_db = SectorDB(db_instance)
        self.current_sector = None
        
    def show_view(self, display_widget):
        """Show the sector view in the given widget.
        
        Args:
            display_widget: The widget to display the sector view in.
        """
        # Check if we're dealing with a stacked widget (main app) or text edit (legacy)
        from PyQt6.QtWidgets import QStackedWidget
        
        if isinstance(display_widget, QStackedWidget):
            # Create our sectors view widget if it doesn't exist
            if not hasattr(self, 'sectors_view_widget'):
                # Use the modern SectorView class
                # Get database path from environment variable
                import os
                from dotenv import load_dotenv
                load_dotenv("config/.env")
                db_path = os.getenv('DATABASE_FILE_PATH', './database/traveller_campaign.db')
                self.sectors_view_widget = SectorView(db_path=db_path)
                # Load sectors from database
                sectors = self.sectors_db.get_all_sectors()
                
                # Set sectors in the SectorView
                self.sectors_view_widget.set_sectors(sectors)
                
                # Connect signals from SectorView
                self.sectors_view_widget.system_selected.connect(self._on_system_selected)
                self.sectors_view_widget.search_requested.connect(self._on_search_requested)
                
                # Add sectors view widget to the stacked widget
                display_widget.addWidget(self.sectors_view_widget)
                display_widget.setCurrentWidget(self.sectors_view_widget)
                
            else:
                # If sectors view widget already exists, just switch to it and refresh data
                sectors = self.db.get_all_sectors()
                self.sectors_view_widget.set_sectors(sectors)
                display_widget.setCurrentWidget(self.sectors_view_widget)
                
        elif isinstance(display_widget, QTextEdit):
            # Instead of trying to set a layout on QTextEdit (which doesn't work properly),
            # we'll display a simple message and create our own window
            display_widget.clear()
            display_widget.setText("Loading sectors...")
            
            # Create our own window for sector display
            self.sector_window = QWidget()
            self.sector_window.setWindowTitle("Sectors")
            layout = QVBoxLayout(self.sector_window)
            
            # Create left panel for search and sector list
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(5, 5, 5, 5)
            
            # Add search box
            search_box = QLineEdit()
            search_box.setPlaceholderText("Search sectors...")
            left_layout.addWidget(search_box)
            
            # Create sectors list widget
            sectors_list = QListWidget()
            sectors_list.setMaximumWidth(300)
            left_layout.addWidget(sectors_list)
            
            # Create right panel for sector details and map
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            
            # Add sector header
            sector_header = QLabel("Select a sector")
            sector_header.setStyleSheet("font-weight: bold; font-size: 16px; color: #00FF00;")
            right_layout.addWidget(sector_header)
            
            # Add sector map view
            map_frame = QFrame()
            map_frame.setFrameShape(QFrame.Shape.StyledPanel)
            map_frame.setMinimumHeight(200)
            map_layout = QVBoxLayout(map_frame)
            
            map_scene = QGraphicsScene()
            map_view = QGraphicsView(map_scene)
            map_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            map_layout.addWidget(map_view)
            
            right_layout.addWidget(map_frame)
            
            # Create systems list and details panel
            systems_splitter = QSplitter(Qt.Orientation.Vertical)
            
            # Systems list widget
            systems_frame = QFrame()
            systems_layout = QVBoxLayout(systems_frame)
            systems_label = QLabel("Systems")
            systems_label.setStyleSheet("color: #00FF00; font-weight: bold;")
            systems_layout.addWidget(systems_label)
            
            systems_list = QListWidget()
            systems_list.setStyleSheet(TERMINAL_STYLE)
            systems_layout.addWidget(systems_list)
            
            # Planet details widget
            planet_frame = QFrame()
            planet_layout = QVBoxLayout(planet_frame)
            planet_header = QLabel("Planet Details")
            planet_header.setStyleSheet("color: #00FF00; font-weight: bold;")
            planet_layout.addWidget(planet_header)
            
            planet_details = QTextEdit()
            planet_details.setReadOnly(True)
            planet_details.setStyleSheet(TERMINAL_STYLE)
            planet_layout.addWidget(planet_details)
            
            # Add to systems splitter
            systems_splitter.addWidget(systems_frame)
            systems_splitter.addWidget(planet_frame)
            systems_splitter.setStretchFactor(0, 1)  # Systems list gets less space
            systems_splitter.setStretchFactor(1, 2)  # Planet details gets more space
            
            # Create sector details widget
            sector_details = QTextEdit()
            sector_details.setReadOnly(True)
            sector_details.setStyleSheet(TERMINAL_STYLE)
            
            # Create info tabs for sector details
            info_tabs = QTabWidget()
            info_tabs.setStyleSheet("background-color: #0A0A0A; color: #00FF00;")
            info_tabs.setObjectName("info_tabs")
            
            # Sector Info tab
            sector_info_tab = QWidget()
            sector_info_layout = QVBoxLayout(sector_info_tab)
            sector_info_layout.addWidget(sector_details)
            info_tabs.addTab(sector_info_tab, "Sector Info")
            
            # Systems tab (for info_tabs)
            systems_tab = QWidget()
            systems_tab.setObjectName("systems_tab")
            systems_tab_layout = QVBoxLayout(systems_tab)
            
            # Systems list widget
            systems_list = QListWidget()
            systems_list.setObjectName("systems_list")
            systems_list.setStyleSheet(TERMINAL_STYLE)
            systems_tab_layout.addWidget(systems_list)
            
            info_tabs.addTab(systems_tab, "Systems")
            
            # Planet details tab (for info_tabs)
            planet_info_tab = QWidget()
            planet_info_tab.setObjectName("planet_info_tab")
            planet_info_layout = QVBoxLayout(planet_info_tab)
            
            # Planet details
            planet_details = QTextEdit()
            planet_details.setObjectName("planet_details")
            planet_details.setReadOnly(True)
            planet_details.setStyleSheet(TERMINAL_STYLE)
            planet_info_layout.addWidget(planet_details)
            
            info_tabs.addTab(planet_info_tab, "Planet Info")
            
            # We're using the MapTabsWidget from SectorView for maps
            # No need to create separate map tabs here
            
            # Add info tabs to the right panel
            # We'll use SectorView's MapTabsWidget for maps
            right_layout.addWidget(info_tabs)
            
            # Create a splitter for left and right panels
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.addWidget(left_panel)
            splitter.addWidget(right_panel)
            splitter.setStretchFactor(0, 1)  # Left panel (list) gets less space
            splitter.setStretchFactor(1, 3)  # Right panel (details) gets more space
            
            # Add splitter to layout
            layout.addWidget(splitter)
            
            # Load sectors from database
            self._load_sectors(sectors_list, sector_details)
            
            # Connect signals
            sectors_list.currentItemChanged.connect(
                lambda current, previous: self._on_sector_selected(
                    current, sector_details, sector_header, map_scene, systems_list, info_tabs
                )
            )
            
            # Connect search box signal
            search_box.textChanged.connect(
                lambda text: self._filter_sectors(text, sectors_list)
            )
            
            # Connect systems list signal
            systems_list.currentItemChanged.connect(
                lambda current, previous: self._on_system_selected(current, planet_details)
            )
            
            # Store references to widgets we need to access later
            self.sectors_list = sectors_list
            self.sector_details = sector_details
            self.sector_header = sector_header
            self.map_scene = map_scene
            self.map_view = map_view
            
            # Show the sector window
            self.sector_window.resize(1000, 600)
            self.sector_window.show()
            
            # Update the main display widget with a message
            display_widget.setText("Sectors view opened in a new window.")
        else:
            logger.error(f"Unsupported display widget type: {type(display_widget)}")
            
    def get_sectors_by_milieu(self, milieu):
        """Get sectors filtered by milieu.
        
        Args:
            milieu: The milieu code to filter by
            
        Returns:
            List of sector records matching the specified milieu
        """
        try:
            # Query all sectors from the database
            all_sectors = self.db.read_records("sectors")
            
            if not all_sectors:
                return []
                
            # Filter sectors by milieu
            filtered_sectors = [s for s in all_sectors if s[7] == milieu]  # Index 7 is milieu
            return filtered_sectors
            
        except Exception as e:
            logger.error(f"Error filtering sectors by milieu: {e}")
            return []
    
    def _load_sectors(self, list_widget, details_widget, milieu=None):
        """Load sectors from the database into the list widget.
        
        Args:
            list_widget: The QListWidget to populate with sectors
            details_widget: The QTextEdit to show sector details
            milieu: Optional milieu code to filter sectors by
        """
        try:
            # Get sectors, filtered by milieu if specified
            if milieu:
                sectors = self.get_sectors_by_milieu(milieu)
            else:
                # Get current milieu preference from settings
                from controller.settings_controller import SettingsController
                settings = SettingsController()
                current_milieu = settings.load_milieu()
                sectors = self.get_sectors_by_milieu(current_milieu)
            
            if not sectors:
                list_widget.addItem("No sectors found for the selected milieu")
                details_widget.setText("No sectors available for the selected milieu. Please add sectors to the database or select a different milieu.")
                return
                
            # Sort sectors by name
            sorted_sectors = sorted(sectors, key=lambda s: s[1] if s[1] else f"ZZZ{s[0]}")  # Sort by name (index 1), fallback to ID for unnamed
            
            # Add sectors to the list widget
            for sector in sorted_sectors:
                sector_id, name, x, y, desc, img_path, abbrev, milieu = sector
                display_name = name if name else f"Unnamed Sector {sector_id}"
                
                # Create item with sector data stored
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "sector_id": sector_id,
                    "name": name,
                    "x_coordinate": x,
                    "y_coordinate": y,
                    "description": desc,
                    "image_path": img_path,
                    "abbreviation": abbrev,
                    "milieu": milieu
                })
                
                list_widget.addItem(item)
                
            # Select the first sector by default
            if list_widget.count() > 0:
                list_widget.setCurrentRow(0)
                
        except Exception as e:
            logger.error(f"Error loading sectors: {e}")
            list_widget.addItem(f"Error: {str(e)}")
            details_widget.setText(f"Failed to load sectors: {str(e)}")
            
    def _filter_sectors(self, search_text, list_widget):
        """Filter the sectors list based on search text.
        
        Args:
            search_text: Text to search for in sector names
            list_widget: The QListWidget containing sector items
        """
        search_text = search_text.lower()
        
        # Show all items if search text is empty
        if not search_text:
            for i in range(list_widget.count()):
                list_widget.item(i).setHidden(False)
            return
            
        # Filter items based on search text
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            sector_data = item.data(Qt.ItemDataRole.UserRole)
            if sector_data:
                # Search in name and abbreviation
                name = sector_data.get('name', '').lower()
                abbrev = sector_data.get('abbreviation', '').lower()
                
                # Show item if search text is in name or abbreviation
                item.setHidden(not (search_text in name or search_text in abbrev))
    
    def _on_sector_selected(self, current_item, details_widget, header_widget, map_scene, systems_list, info_tabs):
        """Handle sector selection from the list.
        
        Args:
            current_item: The selected QListWidgetItem
            details_widget: The QTextEdit widget to display sector details
            header_widget: The QLabel widget for the sector header
            map_scene: The QGraphicsScene for displaying the sector map
            systems_list: Optional QListWidget to display systems in the sector
            details_tabs: Optional QTabWidget to switch to systems tab
        """
        if not current_item:
            return
            
        # Get sector data from the item
        sector_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not sector_data:
            return
            
        # Store the current sector
        self.current_sector = sector_data
        
        # Update header with sector name
        header_widget.setText(sector_data.get('name', 'Unknown Sector'))
        
        # We're not using map_tabs anymore
        map_labels = {}
        
        # Display sector details with enhanced formatting
        details = f"<div style='{DETAILS_DIV_STYLE}'>"
        details += f"<h2 style='color: {TEXT_COLOR};'>{sector_data['name']}</h2>"
        
        # Create a table for sector details
        details += f"<table style='{TABLE_STYLE}'>"
        
        # Add all available sector information
        if sector_data['abbreviation']:
            details += f"<tr><td style='{TABLE_CELL_STYLE}'><b>Abbreviation:</b></td><td>{sector_data['abbreviation']}</td></tr>"
        if sector_data['milieu']:
            details += f"<tr><td style='{TABLE_CELL_STYLE}'><b>Milieu:</b></td><td>{sector_data['milieu']}</td></tr>"
        if sector_data['x_coordinate'] is not None:
            details += f"<tr><td style='{TABLE_CELL_STYLE}'><b>X Coordinate:</b></td><td>{sector_data['x_coordinate']}</td></tr>"
        if sector_data['y_coordinate'] is not None:
            details += f"<tr><td style='{TABLE_CELL_STYLE}'><b>Y Coordinate:</b></td><td>{sector_data['y_coordinate']}</td></tr>"
            
        details += "</table>"
        
        # Add description if available
        if sector_data.get('description'):
            details += f"<h3 style='{SECTION_HEADER_STYLE}'>Description:</h3>"
            details += f"<p>{sector_data['description']}</p>"
        
        details += "</div>"
        
        # Update details widget
        if details_widget:
            details_widget.setHtml(details)
            
        # Update sector map in map scene
        if map_scene:
            self._generate_sector_map(map_scene, sector_data)
            
        # Update sector map if available
        sector_map_label = map_labels.get('sector_map_label')
        if sector_map_label:
            self._update_map_display(sector_map_label, 
                                  sector_data.get('image_path'), 
                                  f"Sector Map: {sector_data['name']}",
                                  f"Error loading map for sector: {sector_data['name']}",
                                  "sector",
                                  sector_data.get('id'))
            
        # Load systems for this sector if systems_list is provided
        if systems_list and self.db:
            self._load_systems_for_sector(sector_data, systems_list, details_tabs)
        
        # Emit signal that sector has changed
        logger.info(f"Emitting sector_changed signal for sector: {sector_data['name']}")
        self.sector_changed.emit(sector_data)
        
    def _find_planet_details_widget(self, parent_list):
        """Find the planet details widget in the UI hierarchy.
        
        Args:
            parent_list: The parent list widget to start searching from
            
        Returns:
            The planet details widget if found, None otherwise
        """
        # Find the main window
        main_window = self._find_parent_window(parent_list)
        if not main_window:
            return None, {}
            
        # Find info tabs
        info_tabs = main_window.findChild(QTabWidget, "info_tabs")
        if not info_tabs:
            return None, {}
            
        # Find map tabs and labels
        map_tabs = main_window.findChild(QTabWidget, "map_tabs")
        map_labels = self._find_map_labels(map_tabs) if map_tabs else {}
        
        # Find planet details widget
        planet_details_widget = None
        planet_info_tab = info_tabs.findChild(QWidget, "planet_info_tab")
        if planet_info_tab:
            planet_details_widget = planet_info_tab.findChild(QTextEdit, "planet_details")
            
        return planet_details_widget, map_labels
    
    def _on_system_selected(self, current_item, planet_details_widget=None):
        """Handle system selection from the list.
        
        Args:
            current_item: The selected QListWidgetItem or system data dictionary
            planet_details_widget: The QTextEdit widget to display planet details
        """
        if not current_item:
            return
            
        # Get system data from item
        system_data = None
        if isinstance(current_item, QListWidgetItem):
            system_data = current_item.data(Qt.ItemDataRole.UserRole)
        else:
            # Assume it's already a system data dictionary
            system_data = current_item
            
        if not system_data:
            return
            
        # Find planet details widget if not provided
        if not planet_details_widget and hasattr(self, 'sectors_view_widget'):
            # _find_planet_details_widget returns a tuple: (widget, map_labels)
            result = self._find_planet_details_widget(self.sectors_view_widget)
            if result:
                planet_details_widget, map_labels = result
            
        # Get planets for this system
        planets = self.db.get_planets_for_system(system_data.get('id'))
        
        # Update planet details
        if planet_details_widget and hasattr(planet_details_widget, 'setHtml'):
            try:
                # Format planet details as HTML
                details_html = self._format_planet_details(system_data, planets)
                planet_details_widget.setHtml(details_html)
            except Exception as e:
                print(f"❌ Error updating planet details: {e}")
        elif planet_details_widget:
            print(f"❌ Planet details widget does not have setHtml method: {type(planet_details_widget)}")
        else:
            print("⚠️ No planet details widget available")
            
    def _update_legacy_system_map(self, system_data, map_labels):
        """Update the legacy system map display if it exists.
        
        Args:
            system_data: Dictionary containing system information
            map_labels: Dictionary of map labels and widgets
        """
        system_map_label = map_labels.get('system_map_label') if map_labels else None
        if system_map_label:
            system_hex = system_data.get('hex', '')
            system_name = system_data.get('main_world', 'Unknown')
            self._update_map_display(
                system_map_label, 
                system_data.get('image_path'), 
                f"System Map: {system_hex} - {system_name}",
                f"Error loading map for system: {system_hex} - {system_name}",
                "system",
                system_data.get('id')
            )
            
    def _format_planet_details(self, system_data, planets):
        """Format planet details as HTML.
        
        Args:
            system_data: Dictionary containing system information
            planets: List of planet dictionaries
            
        Returns:
            HTML string with formatted planet details
        """
        details = f"<div style='{DETAILS_DIV_STYLE}'>"
        details += f"<h3>System: {system_data['hex']} - {system_data.get('main_world', 'Unknown')}</h3>"
        
        # Create a table for planet details
        details += f"<table style='{TABLE_STYLE}'>"
        details += f"<tr style='{TABLE_HEADER_STYLE}'><th>Planet</th><th>UWP</th><th>Starport</th><th>Tech Level</th></tr>"
        
        for planet in planets:
            details += f"<tr><td>{planet.get('name', 'Unknown')}</td>"
            details += f"<td>{planet.get('UWP', '-')}</td>"
            details += f"<td>{planet.get('starport', '-')}</td>"
            details += f"<td>{planet.get('tech_level', '-')}</td></tr>"
        
        details += "</table></div>"
        return details
        
    def _update_planet_details(self, system_data, planets, map_labels, planet_details_widget):
        """Update planet details and map.
        
        Args:
            system_data: Dictionary containing system information
            planets: List of planet dictionaries
            map_labels: Dictionary of map labels and widgets
            planet_details_widget: Widget to display planet details
        """
        if not planets:
            planet_details_widget.setHtml(f"<div style='{DETAILS_DIV_STYLE}'>"
                                        f"<h3>No planets found in system {system_data['hex']}</h3></div>")
            
            # Clear planet map if no planets
            planet_map_label = map_labels.get('planet_map')
            if planet_map_label:
                planet_map_label.setText("No planets in this system")
            return
            
        # Format planet details
        details = self._format_planet_details(system_data, planets)
        
        # Update planet details widget
        planet_details_widget.setHtml(details)
        
        # Find the main world for map display
        main_planet = next((planet for planet in planets if planet.get('name') == system_data.get('main_world')), None)
        
        # Update planet map
        planet_map_label = map_labels.get('planet_map')
        if planet_map_label and main_planet:
            self._update_map_display(planet_map_label, 
                                  main_planet.get('image_path'), 
                                  f"Planet Map: {main_planet.get('name', 'Unknown')}",
                                  f"Error loading map for planet: {main_planet.get('name', 'Unknown')}",
                                  "planet",
                                  main_planet.get('id'))
            
            # Update the planet map in the map tabs widget if available
            if hasattr(self.view, 'map_tabs'):
                self.view.map_tabs.set_planet(main_planet)
    
    def _handle_planet_selected(self, planet):
        """Handle planet selection from the system map or list.
        
        Args:
            planet: Dictionary containing planet information.
        """
        if not planet:
            return
            
        logger.info(f"Planet selected: {planet.get('name', 'Unknown')}")
        
        # Store the selected planet
        self.current_planet = planet
        
        # Update the planet map in the map tabs widget
        if hasattr(self.view, 'map_tabs'):
            self.view.map_tabs.set_planet(planet)
            
        # If we have a planet controller, notify it as well
        if hasattr(self, 'planet_controller'):
            self.planet_controller.set_current_planet(planet)
    
    def _update_map_display(self, map_label, image_path, placeholder_text, error_text, entity_type=None, entity_id=None):
        """Update map display with image or placeholder text.
        
        Args:
            map_label: QLabel widget to update
            image_path: Path to image file
            placeholder_text: Text to display if no image is available
            error_text: Text to display if image loading fails
            entity_type: Type of entity (sector, system, planet) for API fetching
            entity_id: ID of the entity for API fetching and caching
        """
        if image_path and os.path.exists(image_path):
            # Load image from file
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                map_label.setPixmap(pixmap.scaled(
                    map_label.width(), 
                    map_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                map_label.setText(error_text)
        else:
            # If no image or loading failed, try to fetch from API
            if entity_type and entity_id and self.db:
                map_label.setText(f"{placeholder_text}\n\nFetching map from TravellerWorlds API...")
                # Start a background thread to fetch the map
                self._fetch_map_from_api(map_label, entity_type, entity_id, placeholder_text)
            else:
                # If we can't fetch, just show placeholder
                map_label.setText(f"{placeholder_text}\n\nMap would be loaded from TravellerWorlds API")
                
    def _fetch_map_from_api(self, map_label, entity_type, entity_id, placeholder_text):
        """Fetch a map from the TravellerWorlds API and save it locally.
        
        Args:
            map_label: QLabel widget to update with the fetched map
            entity_type: Type of entity (sector, system, planet)
            entity_id: ID of the entity
            placeholder_text: Text to display if fetching fails
        """
        # In a real implementation, this would be an API call
        # For now, we'll simulate a fetch and local save
        
        # Create maps directory if it doesn't exist
        maps_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'maps')
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
            
        # Create subdirectory for entity type
        entity_dir = os.path.join(maps_dir, entity_type + 's')
        if not os.path.exists(entity_dir):
            os.makedirs(entity_dir)
            
        # Define the local path where the map will be saved
        local_path = os.path.join(entity_dir, f"{entity_id}.png")
        
        # In a real implementation, this would be an API call and file save
        # For now, just update the database with the path
        if self.db:
            try:
                # Update the entity's image_path in the database
                table_name = entity_type + 's'
                self.db.update_record(table_name, entity_id, {'image_path': local_path})
                
                # For demo purposes, we'll just show a message that the map would be fetched
                # In a real implementation, we would download the image and then update the label
                map_label.setText(f"{placeholder_text}\n\nMap would be fetched and saved to:\n{local_path}")
                
            except Exception as e:
                logger.error(f"Error updating {entity_type} map path: {e}")
                map_label.setText(f"{placeholder_text}\n\nError fetching map: {str(e)}")
        else:
            map_label.setText(f"{placeholder_text}\n\nNo database connection to save map location")
    
    def _find_parent_window(self, widget):
        """Find the parent window of a widget."""
        parent = widget.parent()
        while parent:
            if isinstance(parent, QWidget) and not parent.parent():
                return parent
            parent = parent.parent()
        return None
        
    def _find_map_labels(self, map_tabs):
        """Find all map-related labels in the UI.
        
        Args:
            map_tabs: The QTabWidget containing the map tabs
            
        Returns:
            Dictionary of UI elements keyed by their object names
        """
        if not map_tabs:
            return {}
            
        result = {}
        
        # Find sector map tab
        sector_map_tab = map_tabs.findChild(QWidget, "sector_map_tab")
        if sector_map_tab:
            sector_map_label = sector_map_tab.findChild(QLabel, "sector_map_label")
            if sector_map_label:
                result['sector_map_label'] = sector_map_label
        
        # Find system map tab
        system_map_tab = map_tabs.findChild(QWidget, "system_map_tab")
        if system_map_tab:
            system_map_label = system_map_tab.findChild(QLabel, "system_map_label")
            if system_map_label:
                result['system_map_label'] = system_map_label
        
        # Find planet map tab
        planet_map_tab = map_tabs.findChild(QWidget, "planet_map_tab")
        if planet_map_tab:
            planet_map_label = planet_map_tab.findChild(QLabel, "planet_map_label")
            if planet_map_label:
                result['planet_map_label'] = planet_map_label
                
        return result

    
    def _load_systems_for_sector(self, sector_data, systems_list, details_tabs):
        """Load systems for the selected sector and populate the systems list.
        
        Args:
            sector_data: Dictionary containing sector information
            systems_list: QListWidget to display systems in the sector
            details_tabs: QTabWidget to switch to systems tab
        """
        # Clear existing systems
        systems_list.clear()
        
        # Load planets for this sector from database
        planets = self.db.read_records(
            'planets',
            {'sector_id': sector_data['sector_id']},
            ['planet_id', 'name', 'hex', 'UWP', 'starport', 'tech_level', 'subsector_id']
        )
        
        # Group planets by subsector and hex (to represent systems)
        systems = {}
        for planet in planets:
            # Use hex as system identifier
            system_key = planet.get('hex', '')
            if not system_key:
                continue
                
            # Create system entry if it doesn't exist
            if system_key not in systems:
                systems[system_key] = {
                    'hex': system_key,
                    'subsector_id': planet.get('subsector_id'),
                    'planets': []
                }
            
            # Add planet to system
            systems[system_key]['planets'].append(planet)
        
        # Add systems to list widget
        for hex_code, system_data in sorted(systems.items()):
            # Create list item for system
            main_planet = system_data['planets'][0] if system_data['planets'] else {}
            display_name = f"{hex_code}: {main_planet.get('name', 'Unknown')}"
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, system_data)
            systems_list.addItem(item)
        
        # If systems were found, switch to systems tab
        if systems and details_tabs and len(systems) > 0:
            details_tabs.setCurrentIndex(1)  # Switch to Systems tab
    
    def _generate_sector_map(self, scene, sector_data):
        """Generate a visual representation of the sector.
        
        Args:
            scene: QGraphicsScene to draw the map on
            sector_data: Dictionary containing sector data
        """
        # Clear any existing items from the scene
        scene.clear()
        
        # Set scene background color
        scene.setBackgroundBrush(Qt.GlobalColor.black)
        
        # Set scene dimensions (standard Traveller sector is 8x10 subsectors)
        scene_width = 400
        scene_height = 320
        scene.setSceneRect(0, 0, scene_width, scene_height)
        
        # Draw sector name as title
        title_text = scene.addText(sector_data['name'])
        title_text.setDefaultTextColor(Qt.GlobalColor.green)
        title_text.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        title_text.setPos(10, 5)
        
        # Add sector abbreviation
        if sector_data['abbreviation']:
            abbrev_text = scene.addText(f"({sector_data['abbreviation']})")
            abbrev_text.setDefaultTextColor(Qt.GlobalColor.green)
            abbrev_text.setFont(QFont(FONT_FAMILY, 10))
            abbrev_text.setPos(scene_width - 80, 5)
        
        # Draw subsector grid (8x10 standard Traveller sector)
        subsector_width = scene_width / 4  # 4 subsectors across
        subsector_height = scene_height / 4  # 4 subsectors down (with space for title)
        
        # Subsector grid
        grid_pen = QPen(Qt.GlobalColor.darkGreen)
        grid_pen.setWidth(1)
        
        # Draw subsector grid
        for i in range(5):  # Horizontal lines (0-4)
            y_pos = 40 + i * subsector_height
            scene.addLine(0, y_pos, scene_width, y_pos, grid_pen)
            
        for i in range(5):  # Vertical lines (0-4)
            x_pos = i * subsector_width
            scene.addLine(x_pos, 40, x_pos, scene_height, grid_pen)
        
        # Label subsectors A-P (standard Traveller notation)
        subsector_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                           'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
        
        for i in range(16):
            row = i // 4
            col = i % 4
            label_text = scene.addText(subsector_labels[i])
            label_text.setDefaultTextColor(Qt.GlobalColor.lightGray)
            label_text.setFont(QFont(FONT_FAMILY, 8))
            label_text.setPos(col * subsector_width + 5, 40 + row * subsector_height + 5)
        
        # If coordinates are available, highlight the sector's position in galactic grid
        if sector_data['x_coordinate'] is not None and sector_data['y_coordinate'] is not None:
            try:
                x = int(sector_data['x_coordinate'])
                y = int(sector_data['y_coordinate'])
                
                # Add galactic position indicator
                galactic_text = scene.addText(f"Galactic Position: ({x},{y})")
                galactic_text.setDefaultTextColor(Qt.GlobalColor.yellow)
                galactic_text.setFont(QFont(FONT_FAMILY, 9))
                galactic_text.setPos(10, scene_height - 20)
                
                # Add a small galactic position indicator
                indicator_size = 60
                indicator_x = scene_width - indicator_size - 10
                indicator_y = 40
                
                # Draw indicator box
                scene.addRect(indicator_x, indicator_y, indicator_size, indicator_size, 
                             QPen(Qt.GlobalColor.yellow), QBrush(Qt.GlobalColor.transparent))
                
                # Draw center point (this sector)
                center_x = indicator_x + indicator_size/2
                center_y = indicator_y + indicator_size/2
                scene.addEllipse(center_x-3, center_y-3, 6, 6, 
                               QPen(Qt.GlobalColor.yellow), 
                               QBrush(Qt.GlobalColor.yellow))
                
                # Label as "Current"
                current_text = scene.addText("Current")
                current_text.setDefaultTextColor(Qt.GlobalColor.yellow)
                current_text.setFont(QFont(FONT_FAMILY, 7))
                current_text.setPos(indicator_x + 5, indicator_y + indicator_size + 5)
                
            except (ValueError, TypeError):
                # Handle invalid coordinate values
                pass
                
    def _on_search_requested(self, search_text):
        """Handle search requests from the sector view.
        
        Args:
            search_text: Text to search for in sector and system names
        """
        if not search_text or not hasattr(self, 'sectors_view_widget'):
            return
            
        # Search for sectors matching the text
        matching_sectors = self.db.search_sectors(search_text)
        
        # Search for systems matching the text
        matching_systems = self.db.search_systems(search_text)
        
        # Update the sector view with search results
        if matching_sectors:
            # If sectors match, show the first matching sector
            self.sectors_view_widget.set_sector(matching_sectors[0])
            
            # If systems also match, filter to show only matching systems
            if matching_systems:
                systems_in_sector = [s for s in matching_systems if s.get('sector_id') == matching_sectors[0].get('id')]
                if systems_in_sector:
                    self.sectors_view_widget.set_systems(systems_in_sector)
        elif matching_systems:
            # If only systems match, show the sector containing the first matching system
            system = matching_systems[0]
            sector_id = system.get('sector_id')
            if sector_id:
                sector = self.db.get_sector_by_id(sector_id)
                if sector:
                    self.sectors_view_widget.set_sector(sector)
                    # Filter to show only matching systems in this sector
                    systems_in_sector = [s for s in matching_systems if s.get('sector_id') == sector_id]
                    self.sectors_view_widget.set_systems(systems_in_sector)