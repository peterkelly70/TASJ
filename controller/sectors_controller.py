import logging
import os
from PyQt6.QtWidgets import (QTextEdit, QVBoxLayout, QListWidget, QListWidgetItem, 
                              QWidget, QSplitter, QLabel, QLineEdit, QHBoxLayout, 
                              QGraphicsView, QGraphicsScene, QFrame, QTabWidget, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QFont, QPen, QBrush, QColor
from view.sector_view import SectorView
from model.sectors_db import SectorDB

# Constants for repeated strings
UNKNOWN_SYSTEM = 'Unknown System'
UNKNOWN_SECTOR = 'Unknown Sector'
NO_SYSTEMS_AVAILABLE = 'No systems available'
NO_SYSTEM_SELECTED = 'No system selected'
NO_SYSTEM_DATA = 'No system data available'

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
        
    def _format_planet_details(self, system_data, planets):
        """Format planet details as HTML.
        
        Args:
            system_data: Dictionary containing system information
            planets: List of planet dictionaries
            
        Returns:
            HTML string with formatted planet details
        """
        if not system_data:
            return "<p>No system data available</p>"
        
        system_name = system_data.get('name', UNKNOWN_SYSTEM)
        system_hex = system_data.get('hex', 'Unknown')
        system_uwp = system_data.get('uwp', 'Unknown')
        
        html = f"""
        <div style="font-family: Courier New; color: #00FF00; background-color: #0A0A0A;">
            <h2 style="color: #AAFFAA;">{system_name}</h2>
            <p><strong>Hex:</strong> {system_hex}</p>
            <p><strong>UWP:</strong> {system_uwp}</p>
        """
        
        if planets:
            html += "<h3 style='color: #AAFFAA;'>Planets:</h3>"
            html += "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr style='color: #AAFFAA;'><th>Name</th><th>Type</th><th>Size</th><th>Atmosphere</th><th>Hydrographics</th><th>Population</th></tr>"
            
            for planet in planets:
                html += f"""
                <tr>
                    <td>{planet.get('name', 'Unknown')}</td>
                    <td>{planet.get('planet_type', 'Unknown')}</td>
                    <td>{planet.get('size', 'Unknown')}</td>
                    <td>{planet.get('atmosphere', 'Unknown')}</td>
                    <td>{planet.get('hydrographics', 'Unknown')}</td>
                    <td>{planet.get('population', 'Unknown')}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p>No planets found for this system.</p>"
        
        html += "</div>"
        return html

    def _format_system_details(self, system_data):
        """Format system details as HTML.
        
        Args:
            system_data: Dictionary containing system information
            
        Returns:
            HTML string with formatted system details
        """
        if not system_data:
            return "<p>No system data available</p>"
        
        system_name = system_data.get('name', UNKNOWN_SYSTEM)
        system_hex = system_data.get('hex', 'Unknown')
        system_uwp = system_data.get('uwp', 'Unknown')
        
        html = f"""
        <div style="font-family: Courier New; color: #00FF00; background-color: #0A0A0A;">
            <h2 style="color: #AAFFAA;">{system_name}</h2>
            <p><strong>Hex:</strong> {system_hex}</p>
            <p><strong>UWP:</strong> {system_uwp}</p>
        """
        
        html += "</div>"
        return html

    def _format_planet_details(self, planet_data):
        """Format planet details as HTML.
        
        Args:
            planet_data: Dictionary containing planet information
            
        Returns:
            HTML string with formatted planet details
        """
        if not planet_data:
            return "<p>No planet data available</p>"
        
        planet_name = planet_data.get('name', 'Unknown Planet')
        planet_type = planet_data.get('planet_type', 'Unknown')
        planet_size = planet_data.get('size', 'Unknown')
        planet_atmosphere = planet_data.get('atmosphere', 'Unknown')
        planet_hydrographics = planet_data.get('hydrographics', 'Unknown')
        planet_population = planet_data.get('population', 'Unknown')
        
        html = f"""
        <div style="font-family: Courier New; color: #00FF00; background-color: #0A0A0A;">
            <h2 style="color: #AAFFAA;">{planet_name}</h2>
            <p><strong>Type:</strong> {planet_type}</p>
            <p><strong>Size:</strong> {planet_size}</p>
            <p><strong>Atmosphere:</strong> {planet_atmosphere}</p>
            <p><strong>Hydrographics:</strong> {planet_hydrographics}</p>
            <p><strong>Population:</strong> {planet_population}</p>
        """
        
        html += "</div>"
        return html

    def _format_sector_details(self, sector_data):
        """Format sector details as HTML.
        
        Args:
            sector_data: Dictionary containing sector information
            
        Returns:
            HTML string with formatted sector details
        """
        if not sector_data:
            return "<p>No sector data available</p>"
        
        sector_name = sector_data.get('name', UNKNOWN_SECTOR)
        location = sector_data.get('location', 'Unknown')
        milieu = sector_data.get('milieu', 'Unknown')
        subsector_count = sector_data.get('subsector_count', '0')
        system_count = sector_data.get('system_count', '0')
        description = sector_data.get('description', 'No description available.')
        
        html = f"""
        <div style="{DETAILS_DIV_STYLE}">
            <h2 style="{SECTION_HEADER_STYLE}">{sector_name}</h2>
            <hr style="{SEPARATOR_STYLE}">
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Milieu:</strong> {milieu}</p>
            <p><strong>Subsector Count:</strong> {subsector_count}</p>
            <p><strong>System Count:</strong> {system_count}</p>
            <hr style="{SEPARATOR_STYLE}">
            <h3 style="{SECTION_HEADER_STYLE}">Description:</h3>
            <p>{description}</p>
        </div>
        """
        
        return html

    def _on_system_selected(self, current_item, system_details_widget=None, system_header_widget=None, system_map_scene=None, planet_list_widget=None):
        """Handle system selection from the list.
        
        Args:
            current_item: The selected QListWidgetItem or system data dictionary
            system_details_widget: The QTextEdit widget to display system details
            system_header_widget: The QLabel widget for the system header
            system_map_scene: The QGraphicsScene for the system map
            planet_list_widget: The QListWidget for planets in the system
        """
        try:
            # Check if we have a valid widget to display details
            if not system_details_widget or not hasattr(system_details_widget, 'setHtml'):
                return
                
            if isinstance(current_item, dict):
                system_data = current_item
            elif current_item is None:
                # Handle case when no item is selected
                if system_details_widget:
                    system_details_widget.setHtml(f"<p>{NO_SYSTEM_SELECTED}</p>")
                if system_header_widget:
                    system_header_widget.setText("Select a system")
                if planet_list_widget:
                    planet_list_widget.clear()
                return
            else:
                # Handle QListWidgetItem
                system_data = current_item.data(Qt.ItemDataRole.UserRole)
            
            if not system_data:
                # Handle empty system data
                if system_details_widget:
                    system_details_widget.setHtml(f"<p>{NO_SYSTEM_DATA}</p>")
                if system_header_widget:
                    system_header_widget.setText("No system data")
                if planet_list_widget:
                    planet_list_widget.clear()
                return
                
            # Store the current system
            self.current_system = system_data
            
            # Update the header
            system_name = system_data.get('name', UNKNOWN_SYSTEM)
            if system_header_widget:
                system_header_widget.setText(f"System: {system_name}")
            
            # Format system details
            system_details = self._format_system_details(system_data)
            
            # Update the system details widget
            if system_details_widget:
                system_details_widget.setHtml(system_details)
                
            # Update the system map if available
            if system_map_scene:
                system_map_scene.clear()
                self._draw_system_map(system_data, system_map_scene)
                
            # Update planet list if available
            if planet_list_widget:
                planet_list_widget.clear()
                
                # Get planets for this system
                system_id = system_data.get('id')
                if system_id:
                    planets = self.sectors_db.get_planets_for_system(system_id)
                    
                    if planets:
                        for planet in planets:
                            planet_name = planet.get('name', 'Unknown Planet')
                            item = QListWidgetItem(planet_name)
                            item.setData(Qt.ItemDataRole.UserRole, planet)
                            planet_list_widget.addItem(item)
                    else:
                        # No planets available
                        empty_item = QListWidgetItem("No planets available")
                        empty_item.setData(Qt.ItemDataRole.UserRole, None)
                        planet_list_widget.addItem(empty_item)
            
        except Exception as e:
            logger.error(f"Error in _on_system_selected: {e}")
            
    def _on_planet_selected(self, current_item, planet_details_widget=None, planet_header_widget=None, planet_map_scene=None):
        """Handle planet selection from the list.
        
        Args:
            current_item: The selected QListWidgetItem or planet data dictionary
            planet_details_widget: The QTextEdit widget to display planet details
            planet_header_widget: The QLabel widget for the planet header
            planet_map_scene: The QGraphicsScene for the planet map
        """
        try:
            # Check if we have a valid widget to display details
            if not planet_details_widget or not hasattr(planet_details_widget, 'setHtml'):
                return
                
            if isinstance(current_item, dict):
                planet_data = current_item
            elif current_item is None:
                # Handle case when no item is selected
                if planet_details_widget:
                    planet_details_widget.setHtml("<p>No planet selected</p>")
                if planet_header_widget:
                    planet_header_widget.setText("Select a planet")
                return
            else:
                # Handle QListWidgetItem
                planet_data = current_item.data(Qt.ItemDataRole.UserRole)
            
            if not planet_data:
                # Handle empty planet data
                if planet_details_widget:
                    planet_details_widget.setHtml("<p>No planet data available</p>")
                if planet_header_widget:
                    planet_header_widget.setText("No planet data")
                return
                
            # Store the current planet
            self.current_planet = planet_data
            
            # Update the header
            planet_name = planet_data.get('name', 'Unknown Planet')
            if planet_header_widget:
                planet_header_widget.setText(f"Planet: {planet_name}")
            
            # Format planet details
            planet_details = self._format_planet_details(planet_data)
            
            # Update the planet details widget
            if planet_details_widget:
                planet_details_widget.setHtml(planet_details)
                
            # Update the planet map if available
            if planet_map_scene:
                planet_map_scene.clear()
                self._draw_planet_map(planet_data, planet_map_scene)
            
        except Exception as e:
            logger.error(f"Error in _on_planet_selected: {e}")
            
    def _draw_system_map(self, system_data, scene):
        """Draw a system map in the given scene.
        
        Args:
            system_data: Dictionary containing system information
            scene: QGraphicsScene to draw the map in
        """
        try:
            if not system_data or not scene:
                return
                
            # Clear the scene
            scene.clear()
            
            # Get system data
            system_name = system_data.get('name', UNKNOWN_SYSTEM)
            planets = system_data.get('planets', [])
            
            # Add system name as text
            text_item = QGraphicsTextItem(f"System: {system_name}")
            text_item.setDefaultTextColor(QColor(0, 255, 0))  # Green text
            scene.addItem(text_item)
            
            # Draw the star at the center
            star_radius = 20
            star = QGraphicsEllipseItem(0, 0, star_radius * 2, star_radius * 2)
            star.setBrush(QBrush(QColor(255, 255, 0)))  # Yellow star
            star.setPos(scene.width() / 2 - star_radius, scene.height() / 2 - star_radius)
            scene.addItem(star)
            
            # Draw planets in orbits around the star
            if planets:
                orbit_spacing = 40  # Space between orbits
                for i, planet in enumerate(planets):
                    orbit_radius = star_radius * 2 + (i + 1) * orbit_spacing
                    
                    # Draw orbit
                    orbit = QGraphicsEllipseItem(
                        scene.width() / 2 - orbit_radius,
                        scene.height() / 2 - orbit_radius,
                        orbit_radius * 2,
                        orbit_radius * 2
                    )
                    orbit.setPen(QPen(QColor(100, 100, 100)))  # Gray orbit
                    scene.addItem(orbit)
                    
                    # Draw planet
                    planet_radius = 10
                    planet_item = QGraphicsEllipseItem(0, 0, planet_radius * 2, planet_radius * 2)
                    
                    # Determine planet color based on type
                    planet_type = planet.get('planet_type', '').lower()
                    if 'gas' in planet_type:
                        color = QColor(200, 200, 255)  # Light blue for gas giants
                    elif 'water' in planet_type or 'ocean' in planet_type:
                        color = QColor(0, 0, 255)  # Blue for water worlds
                    elif 'desert' in planet_type:
                        color = QColor(255, 200, 100)  # Tan for desert worlds
                    elif 'ice' in planet_type:
                        color = QColor(200, 255, 255)  # Light cyan for ice worlds
                    else:
                        color = QColor(100, 200, 100)  # Green for terrestrial planets
                        
                    planet_item.setBrush(QBrush(color))
                    
                    # Position planet on its orbit at a random angle
                    import math
                    import random
                    angle = random.uniform(0, 2 * math.pi)
                    planet_x = scene.width() / 2 + orbit_radius * math.cos(angle) - planet_radius
                    planet_y = scene.height() / 2 + orbit_radius * math.sin(angle) - planet_radius
                    planet_item.setPos(planet_x, planet_y)
                    
                    scene.addItem(planet_item)
                    
                    # Add planet name
                    planet_name = planet.get('name', f"Planet {i+1}")
                    name_item = QGraphicsTextItem(planet_name)
                    name_item.setDefaultTextColor(QColor(200, 200, 200))  # Light gray text
                    name_item.setPos(planet_x, planet_y + planet_radius * 2 + 5)
                    scene.addItem(name_item)
            else:
                # No planets message
                no_planets_text = QGraphicsTextItem("No planets in this system")
                no_planets_text.setDefaultTextColor(QColor(200, 200, 200))  # Light gray text
                no_planets_text.setPos(scene.width() / 2 - 100, scene.height() / 2 + 50)
                scene.addItem(no_planets_text)
                
        except Exception as e:
            logger.error(f"Error drawing system map: {e}")
            # Add error message to the scene
            error_text = QGraphicsTextItem(f"Error drawing map: {str(e)}")
            error_text.setDefaultTextColor(QColor(255, 0, 0))  # Red text
            scene.addItem(error_text)
            
    def _draw_planet_map(self, planet_data, scene):
        """Draw a planet map in the given scene.
        
        Args:
            planet_data: Dictionary containing planet information
            scene: QGraphicsScene to draw the map in
        """
        try:
            if not planet_data or not scene:
                return
                
            # Clear the scene
            scene.clear()
            
            # Get planet data
            planet_name = planet_data.get('name', 'Unknown Planet')
            planet_type = planet_data.get('planet_type', 'Unknown')
            planet_size = planet_data.get('size', '?')
            planet_atmosphere = planet_data.get('atmosphere', '?')
            planet_hydrographics = planet_data.get('hydrographics', '?')
            
            # Add planet name as text
            text_item = QGraphicsTextItem(f"Planet: {planet_name}")
            text_item.setDefaultTextColor(QColor(0, 255, 0))  # Green text
            scene.addItem(text_item)
            
            # Draw the planet
            planet_radius = 100
            planet = QGraphicsEllipseItem(0, 0, planet_radius * 2, planet_radius * 2)
            
            # Determine planet color based on type
            if 'gas' in planet_type.lower():
                color = QColor(200, 200, 255)  # Light blue for gas giants
                # Add some bands
                gradient = QRadialGradient(planet_radius, planet_radius, planet_radius)
                gradient.setColorAt(0, QColor(220, 220, 255))
                gradient.setColorAt(0.5, QColor(200, 200, 255))
                gradient.setColorAt(1, QColor(180, 180, 235))
                planet.setBrush(QBrush(gradient))
            elif 'water' in planet_type.lower() or 'ocean' in planet_type.lower():
                # Create a blue planet with some green continents
                gradient = QRadialGradient(planet_radius, planet_radius, planet_radius)
                gradient.setColorAt(0, QColor(0, 100, 255))
                gradient.setColorAt(0.7, QColor(0, 80, 200))
                gradient.setColorAt(1, QColor(0, 50, 150))
                planet.setBrush(QBrush(gradient))
            elif 'desert' in planet_type.lower():
                # Create a tan desert planet
                gradient = QRadialGradient(planet_radius, planet_radius, planet_radius)
                gradient.setColorAt(0, QColor(255, 220, 150))
                gradient.setColorAt(0.7, QColor(255, 200, 100))
                gradient.setColorAt(1, QColor(200, 150, 50))
                planet.setBrush(QBrush(gradient))
            elif 'ice' in planet_type.lower():
                # Create an ice planet
                gradient = QRadialGradient(planet_radius, planet_radius, planet_radius)
                gradient.setColorAt(0, QColor(255, 255, 255))
                gradient.setColorAt(0.7, QColor(220, 240, 255))
                gradient.setColorAt(1, QColor(200, 220, 255))
                planet.setBrush(QBrush(gradient))
            else:
                # Default to an Earth-like planet
                gradient = QRadialGradient(planet_radius, planet_radius, planet_radius)
                gradient.setColorAt(0, QColor(100, 200, 100))
                gradient.setColorAt(0.7, QColor(80, 180, 80))
                gradient.setColorAt(1, QColor(50, 150, 50))
                planet.setBrush(QBrush(gradient))
            
            # Position planet in center of scene
            planet.setPos(scene.width() / 2 - planet_radius, scene.height() / 2 - planet_radius)
            scene.addItem(planet)
            
            # Add planet details below
            details_text = f"Type: {planet_type}\nSize: {planet_size}\nAtmosphere: {planet_atmosphere}\nHydrographics: {planet_hydrographics}"
            details_item = QGraphicsTextItem(details_text)
            details_item.setDefaultTextColor(QColor(200, 200, 200))  # Light gray text
            details_item.setPos(scene.width() / 2 - 100, scene.height() / 2 + planet_radius + 20)
            scene.addItem(details_item)
            
        except Exception as e:
            logger.error(f"Error drawing planet map: {e}")
            # Add error message to the scene
            error_text = QGraphicsTextItem(f"Error drawing map: {str(e)}")
            error_text.setDefaultTextColor(QColor(255, 0, 0))  # Red text
            scene.addItem(error_text)
            
    def show_view(self, display_widget):
        """Show the sector view in the given widget with the new layout design.
        
        Args:
            display_widget: The widget to display the sector view in.
        """
        # Create a splitter for the main layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ===== LEFT PANEL =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(300)  # Set minimum width for left panel
    
        # --- SECTOR SELECTOR SECTION ---
        sector_section = QGroupBox("Sectors")
        sector_layout = QVBoxLayout(sector_section)
    
        # Sector search box
        sector_search_layout = QHBoxLayout()
        sector_search_label = QLabel("Search Sectors:")
        sector_search_label.setStyleSheet(HEADER_STYLE)
        sector_search_input = QLineEdit()
        sector_search_input.setStyleSheet(TERMINAL_STYLE)
        sector_search_input.setPlaceholderText("Type to search sectors...")
        sector_search_layout.addWidget(sector_search_label)
        sector_search_layout.addWidget(sector_search_input)
        sector_layout.addLayout(sector_search_layout)
    
        # Sector list
        sector_list = QListWidget()
        sector_list.setStyleSheet(TERMINAL_STYLE)
        sector_list.setSortingEnabled(True)  # Enable alphabetical sorting
        sector_layout.addWidget(sector_list)
        
        # --- SYSTEM SELECTOR SECTION ---
        system_section = QGroupBox("Systems")
        system_layout = QVBoxLayout(system_section)
        
        # System search box
        system_search_layout = QHBoxLayout()
        system_search_label = QLabel("Search Systems:")
        system_search_label.setStyleSheet(HEADER_STYLE)
        system_search_input = QLineEdit()
        system_search_input.setStyleSheet(TERMINAL_STYLE)
        system_search_input.setPlaceholderText("Type to search systems...")
        system_search_layout.addWidget(system_search_label)
        system_search_layout.addWidget(system_search_input)
        system_layout.addLayout(system_search_layout)
        
        # System list
        system_list = QListWidget()
        system_list.setStyleSheet(TERMINAL_STYLE)
        system_list.setSortingEnabled(True)  # Enable alphabetical sorting
        system_layout.addWidget(system_list)
        
        # Add sections to left panel
        left_layout.addWidget(sector_section, 1)  # 1 part for sectors
        left_layout.addWidget(system_section, 1)  # 1 part for systems
        
        # ===== RIGHT PANEL =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # --- MAP SECTION ---
        map_section = QGroupBox("Maps")
        map_layout = QVBoxLayout(map_section)
        
        # Map tabs
        map_tabs = QTabWidget()
        map_tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #004400; }")
        
        # Galactic Map tab
        galactic_map_tab = QWidget()
        galactic_map_layout = QVBoxLayout(galactic_map_tab)
        galactic_map_view = QGraphicsView()
        galactic_map_view.setStyleSheet(MAP_PLACEHOLDER_STYLE)
        galactic_map_scene = QGraphicsScene()
        galactic_map_view.setScene(galactic_map_scene)
        galactic_map_layout.addWidget(galactic_map_view)
        map_tabs.addTab(galactic_map_tab, "Galactic Map")
        
        # Sector Map tab
        sector_map_tab = QWidget()
        sector_map_layout = QVBoxLayout(sector_map_tab)
        sector_map_view = QGraphicsView()
        sector_map_view.setStyleSheet(MAP_PLACEHOLDER_STYLE)
        sector_map_scene = QGraphicsScene()
        sector_map_view.setScene(sector_map_scene)
        sector_map_layout.addWidget(sector_map_view)
        map_tabs.addTab(sector_map_tab, "Sector Map")
        
        # System Map tab
        system_map_tab = QWidget()
        system_map_layout = QVBoxLayout(system_map_tab)
        system_map_view = QGraphicsView()
        system_map_view.setStyleSheet(MAP_PLACEHOLDER_STYLE)
        system_map_scene = QGraphicsScene()
        system_map_view.setScene(system_map_scene)
        system_map_layout.addWidget(system_map_view)
        map_tabs.addTab(system_map_tab, "System Map")
        
        # Planet Map tab
        planet_map_tab = QWidget()
        planet_map_layout = QVBoxLayout(planet_map_tab)
        planet_map_view = QGraphicsView()
        planet_map_view.setStyleSheet(MAP_PLACEHOLDER_STYLE)
        planet_map_scene = QGraphicsScene()
        planet_map_view.setScene(planet_map_scene)
        planet_map_layout.addWidget(planet_map_view)
        map_tabs.addTab(planet_map_tab, "Planet Map")
        
        map_layout.addWidget(map_tabs)
        
        # --- INFO SECTION ---
        info_section = QGroupBox("Information")
        info_layout = QVBoxLayout(info_section)
        
        # Create a splitter for the three info boxes
        info_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sector info box
        sector_info_group = QGroupBox("Sector Info")
        sector_info_layout = QVBoxLayout(sector_info_group)
        sector_header = QLabel("Select a sector")
        sector_header.setStyleSheet(HEADER_STYLE)
        sector_details = QTextEdit()
        sector_details.setReadOnly(True)
        sector_details.setStyleSheet(TERMINAL_STYLE)
        sector_info_layout.addWidget(sector_header)
        sector_info_layout.addWidget(sector_details)
        info_splitter.addWidget(sector_info_group)
        
        # System info box with system description
        system_info_group = QGroupBox("System Info")
        system_info_layout = QVBoxLayout(system_info_group)
        system_header = QLabel("System Description")
        system_header.setStyleSheet(HEADER_STYLE)
        system_details = QTextEdit()
        system_details.setReadOnly(True)
        system_details.setStyleSheet(TERMINAL_STYLE)
        system_info_layout.addWidget(system_header)
        system_info_layout.addWidget(system_details)
        
        # Planet list and details in system info
        planet_list_label = QLabel("Planets:")
        planet_list_label.setStyleSheet(HEADER_STYLE)
        planet_list = QListWidget()
        planet_list.setStyleSheet(TERMINAL_STYLE)
        planet_list.setSortingEnabled(True)  # Enable alphabetical sorting
        planet_list.setMaximumHeight(150)  # Limit height
        system_info_layout.addWidget(planet_list_label)
        system_info_layout.addWidget(planet_list)
        
        # Planet details section within system info
        planet_details_label = QLabel("Planet Details:")
        planet_details_label.setStyleSheet(HEADER_STYLE)
        planet_details = QTextEdit()
        planet_details.setReadOnly(True)
        planet_details.setStyleSheet(TERMINAL_STYLE)
        system_info_layout.addWidget(planet_details_label)
        system_info_layout.addWidget(planet_details)
        
        info_splitter.addWidget(system_info_group)
        
        # Set sizes for info boxes
        info_splitter.setSizes([300, 700])
        
        info_layout.addWidget(info_splitter)
        
        # Add sections to right panel with more space for maps
        right_layout.addWidget(map_section, 3)  # 3 parts for maps (larger proportion)
        right_layout.addWidget(info_section, 1)  # 1 part for info (smaller proportion)
        
        # Add panels to main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Set initial sizes to maximize map space
        main_splitter.setSizes([250, 750])
        
        # Add the splitter to the display widget
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins for more space
        
        # Clear any existing layout
        if display_widget.layout():
            # Remove all widgets from the layout
            while display_widget.layout().count():
                item = display_widget.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            # Delete the layout
            QWidget().setLayout(display_widget.layout())
            
        display_widget.setLayout(layout)
        
        # Connect signals
        sector_search_input.textChanged.connect(lambda text: self._filter_sectors(text, sector_list))
        system_search_input.textChanged.connect(lambda text: self._filter_systems(text, system_list))
        
        sector_list.currentItemChanged.connect(
            lambda current, previous: self._on_sector_selected(
                current, sector_details, sector_header, sector_map_scene, system_list, system_header
            )
        )
        
        system_list.currentItemChanged.connect(
            lambda current, previous: self._on_system_selected(
                current, system_details, system_header, system_map_scene, planet_list
            )
        )
        
        planet_list.currentItemChanged.connect(
            lambda current, previous: self._on_planet_selected(
                current, planet_details, planet_header, planet_map_scene
            )
        )
        
        # Load sectors
        self._load_sectors(sector_list, sector_details)
        
        # Store reference to the sector view widget
        self.sectors_view_widget = SectorView(parent=display_widget)
        
        # Set up the sector view components after initialization
        self.sectors_view_widget.set_db_path(self.db.db_path)
        
        # Store references to important widgets for later use
        self.sector_list = sector_list
        self.system_list = system_list
        self.planet_list = planet_list
        self.sector_details = sector_details
        self.system_details = system_details
        self.planet_details = planet_details
        self.sector_header = sector_header
        self.system_header = system_header
        self.planet_header = planet_header
        self.sector_map_scene = sector_map_scene
        self.system_map_scene = system_map_scene
        self.planet_map_scene = planet_map_scene
        self.galactic_map_scene = galactic_map_scene
        
    def get_sectors_by_milieu(self, milieu):
        """Get sectors filtered by milieu.
        
        Args:
            milieu: The milieu code to filter by
            
        Returns:
            List of sector records matching the specified milieu
        """
        try:
            # Query the database for sectors with the specified milieu
            sectors = self.sectors_db.get_sectors_by_milieu(milieu)
            
            if not sectors:
                logger.warning(f"No sectors found for milieu: {milieu}")
                return []
                
            return sectors
            
        except Exception as e:
            logger.error(f"Error getting sectors by milieu: {e}")
            return []
            
    def _load_sectors(self, list_widget, details_widget, milieu=None):
        """Load sectors from the database into the list widget.
        
        Args:
            list_widget: The QListWidget to populate with sectors
            details_widget: The QTextEdit to show sector details
            milieu: Optional milieu code to filter sectors by
        """
        try:
            # Clear the list
            list_widget.clear()
            
            # Get sectors from the database
            if milieu:
                sectors = self.sectors_db.get_sectors_by_milieu(milieu)
            else:
                sectors = self.sectors_db.get_all_sectors()
                
            if not sectors:
                logger.warning("No sectors found in database")
                return
                
            # Add sectors to the list
            for sector in sectors:
                sector_name = sector.get('name', UNKNOWN_SECTOR)
                item = QListWidgetItem(sector_name)
                item.setData(Qt.ItemDataRole.UserRole, sector)
                list_widget.addItem(item)
                
            # Select the first item
            if list_widget.count() > 0:
                list_widget.setCurrentRow(0)
                
        except Exception as e:
            logger.error(f"Error loading sectors: {e}")
            
    def _filter_sectors(self, text, list_widget):
        """Filter sectors by name based on search text.
        
        Args:
            text: The search text
            list_widget: The QListWidget to filter
        """
        try:
            # Get all sectors
            sectors = self.sectors_db.get_all_sectors()
            
            # Clear the list
            list_widget.clear()
            
            if not text:
                # If no search text, show all sectors
                for sector in sectors:
                    sector_name = sector.get('name', UNKNOWN_SECTOR)
                    item = QListWidgetItem(sector_name)
                    item.setData(Qt.ItemDataRole.UserRole, sector)
                    list_widget.addItem(item)
            else:
                # Filter sectors by name
                for sector in sectors:
                    sector_name = sector.get('name', UNKNOWN_SECTOR)
                    if text.lower() in sector_name.lower():
                        item = QListWidgetItem(sector_name)
                        item.setData(Qt.ItemDataRole.UserRole, sector)
                        list_widget.addItem(item)
                    
        except Exception as e:
            logger.error(f"Error filtering sectors: {e}")
        
        # Sort the list alphabetically
        list_widget.sortItems()
        
    def _filter_systems(self, text, list_widget):
        """Filter systems by name based on search text.
        
        Args:
            text: The search text
            list_widget: The QListWidget to filter
        """
        try:
            # Check if we have a current sector
            if not hasattr(self, 'current_sector') or not self.current_sector:
                return
                
            sector_id = self.current_sector.get('id')
            if not sector_id:
                return
                
            # Get systems for the current sector
            systems = self.sectors_db.get_systems_for_sector(sector_id)
            
            # Clear the list
            list_widget.clear()
            
            if not systems:
                # No systems available
                empty_item = QListWidgetItem(NO_SYSTEMS_AVAILABLE)
                empty_item.setData(Qt.ItemDataRole.UserRole, None)
                list_widget.addItem(empty_item)
                return
                
            if not text:
                # If no search text, show all systems for this sector
                for system in systems:
                    system_name = system.get('name', UNKNOWN_SYSTEM)
                    item = QListWidgetItem(system_name)
                    item.setData(Qt.ItemDataRole.UserRole, system)
                    list_widget.addItem(item)
            else:
                # Filter systems by name
                for system in systems:
                    system_name = system.get('name', UNKNOWN_SYSTEM)
                    if text.lower() in system_name.lower():
                        item = QListWidgetItem(system_name)
                        item.setData(Qt.ItemDataRole.UserRole, system)
                        list_widget.addItem(item)
                    
        except Exception as e:
            logger.error(f"Error filtering systems: {e}")
        
        # Sort the list alphabetically
        list_widget.sortItems()
            
    def _populate_systems_for_sector(self, sector_data):
        """Populate all systems and planets for a sector from API data.
        
        Args:
            sector_data: Dictionary containing sector information
        """
        try:
            sector_id = sector_data.get('id')
            if not sector_id:
                logger.error("No sector ID provided for populating systems")
                return
                
            # Get systems for this sector
            systems = self.sectors_db.get_systems_for_sector(sector_id)
            
            if not systems:
                logger.warning(f"No systems found for sector ID: {sector_id}")
                return
                
            # For each system, get and store its planets
            for system in systems:
                system_id = system.get('id')
                if system_id:
                    # Check if planets already exist for this system
                    existing_planets = self.sectors_db.get_planets_for_system(system_id)
                    
                    if not existing_planets:
                        # Fetch planets from API or generate them
                        planets = self.sectors_db.generate_planets_for_system(system)
                        
                        # Store planets in database
                        if planets:
                            for planet in planets:
                                self.sectors_db.add_planet(planet)
                                
        except Exception as e:
            logger.error(f"Error populating systems for sector: {e}")
            
    def _filter_sectors(self, search_text, list_widget):
        """Filter the sectors list based on search text.
        
        Args:
            search_text: Text to search for in sector names
            list_widget: The QListWidget containing sector items
        """
        # Show all items if search text is empty
        if not search_text:
            for i in range(list_widget.count()):
                list_widget.item(i).setHidden(False)
            return
            
        # Hide items that don't match the search text
        search_text = search_text.lower()
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item_text = item.text().lower()
            item.setHidden(search_text not in item_text)
            
    def _on_sector_selected(self, current_item, details_widget=None, header_widget=None, map_scene=None, systems_list=None, system_header=None):
        """Handle sector selection from the list.
        
        Args:
            current_item: The selected QListWidgetItem
            details_widget: The QTextEdit widget to display sector details
            header_widget: The QLabel widget for the sector header
            map_scene: The QGraphicsScene for the sector map
            systems_list: The QListWidget for systems in the sector
            system_header: The QLabel widget for the system header
        """
        try:
            # Check if we have a valid item
            if not current_item:
                if header_widget:
                    header_widget.setText("Select a sector")
                if details_widget:
                    details_widget.setHtml("<p>No sector selected</p>")
                if systems_list:
                    systems_list.clear()
                if system_header:
                    system_header.setText("Select a system")
                return
                
            # Get the sector data from the item
            sector_data = current_item.data(Qt.ItemDataRole.UserRole)
            if not sector_data:
                if header_widget:
                    header_widget.setText("No sector data")
                if details_widget:
                    details_widget.setHtml("<p>No sector data available</p>")
                if systems_list:
                    systems_list.clear()
                if system_header:
                    system_header.setText("Select a system")
                return
                
            # Store the current sector
            self.current_sector = sector_data
            
            # Update the sector header
            if header_widget:
                sector_name = sector_data.get('name', UNKNOWN_SECTOR)
                header_widget.setText(f"Sector: {sector_name}")
            
            # Format and display sector details
            if details_widget:
                sector_details = self._format_sector_details(sector_data)
                details_widget.setHtml(sector_details)
            
            # Update the sector map
            if map_scene:
                map_scene.clear()
                self._draw_sector_map(sector_data, map_scene)
            
            # Get systems for this sector
            sector_id = sector_data.get('id')
            if sector_id:
                # Load systems into the systems list
                systems = self.sectors_db.get_systems_for_sector(sector_id)
                
                # Clear the systems list
                if systems_list:
                    systems_list.clear()
                if systems:
                    for system in systems:
                        system_name = system.get('name', UNKNOWN_SYSTEM)
                        item = QListWidgetItem(system_name)
                        item.setData(Qt.ItemDataRole.UserRole, system)
                        systems_list.addItem(item)
                        
                    # Switch to the systems tab
                    info_tabs.setCurrentIndex(2)  # Index 2 should be the Systems tab
                    
                    # Select the first system
                    if systems_list.count() > 0:
                        systems_list.setCurrentRow(0)
                else:
                    # Handle case where sector has no systems
                    info_tabs.setCurrentIndex(0)  # Switch to Details tab
                    empty_item = QListWidgetItem("No systems available")
                    empty_item.setData(Qt.ItemDataRole.UserRole, None)
                    systems_list.addItem(empty_item)
            
            # Emit the sector_changed signal with the sector data
            self.sector_changed.emit(sector_data)
        except Exception as e:
            logger.error(f"Error handling sector selection: {e}")
            if header_widget:
                header_widget.setText("Error loading sector")
            if details_widget:
                details_widget.setHtml(f"<p>Error: {e}</p>")
            if systems_list:
                systems_list.clear()
            if system_header:
                system_header.setText("Select a system")
    def _draw_sector_map(self, sector_data, scene):
        """Draw the sector map in the given scene.
        
        Args:
            sector_data: Dictionary containing sector information
            scene: QGraphicsScene to draw the map in
        """
        try:
            # Clear the scene
            scene.clear()
            
            # Get sector dimensions
            sector_width = 800
            sector_height = 600
            
            # Set scene size
            scene.setSceneRect(0, 0, sector_width, sector_height)
            
            # Draw background
            scene.addRect(0, 0, sector_width, sector_height, 
                         QPen(Qt.GlobalColor.darkGreen), 
                         QBrush(QColor(10, 20, 10)))
            
            # Get systems for this sector
            sector_id = sector_data.get('id')
            if not sector_id:
                return
                
            systems = self.sectors_db.get_systems_for_sector(sector_id)
            
            if not systems:
                # Add placeholder text
                text = scene.addText("No systems data available")
                text.setDefaultTextColor(Qt.GlobalColor.green)
                text.setPos(sector_width/2 - 100, sector_height/2 - 10)
                return
                
            # Calculate grid size
            grid_size = min(sector_width / 10, sector_height / 10)
            
            # Draw grid
            pen = QPen(QColor(0, 100, 0))
            for x in range(0, sector_width, int(grid_size)):
                scene.addLine(x, 0, x, sector_height, pen)
            for y in range(0, sector_height, int(grid_size)):
                scene.addLine(0, y, sector_width, y, pen)
                
            # Add coordinate labels
            for i in range(10):
                # Horizontal labels (numbers)
                label = scene.addText(str(i))
                label.setDefaultTextColor(Qt.GlobalColor.green)
                label.setPos(i * grid_size + grid_size/2, 5)
                
                # Vertical labels (letters)
                label = scene.addText(chr(65 + i))  # A, B, C, ...
                label.setDefaultTextColor(Qt.GlobalColor.green)
                label.setPos(5, i * grid_size + grid_size/2)
                
            # Draw systems
            for system in systems:
                try:
                    # Get hex coordinates
                    hex_coord = system.get('hex', '')
                    if not hex_coord or len(hex_coord) < 4:
                        continue
                        
                    # Parse hex coordinates (format: XXYY)
                    x = int(hex_coord[0:2])
                    y = int(hex_coord[2:4])
                    
                    # Calculate position on grid
                    pos_x = x * grid_size
                    pos_y = y * grid_size
                    
                    # Draw system dot
                    dot_size = 10
                    scene.addEllipse(pos_x - dot_size/2, pos_y - dot_size/2, dot_size, dot_size, 
                                   QPen(Qt.GlobalColor.yellow), 
                                   QBrush(Qt.GlobalColor.yellow))
                    
                    # Add system name
                    system_name = system.get('name', 'Unknown')
                    text = scene.addText(system_name)
                    text.setDefaultTextColor(Qt.GlobalColor.green)
                    text.setFont(QFont(FONT_FAMILY, 7))
                    text.setPos(pos_x + 5, pos_y - 15)
                    
                except (ValueError, TypeError):
                    # Skip systems with invalid coordinates
                    continue
                    
            # Add sector name at the top
            sector_name = sector_data.get('name', UNKNOWN_SECTOR)
            title = scene.addText(sector_name)
            title.setDefaultTextColor(Qt.GlobalColor.green)
            title.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            title.setPos(10, 10)
            
            # Add galactic coordinates if available
            galactic_coords = sector_data.get('location', '')
            if galactic_coords:
                try:
                    scene_height = sector_height
                    galactic_text = scene.addText(f"Galactic: {galactic_coords}")
                    galactic_text.setDefaultTextColor(Qt.GlobalColor.green)
                    galactic_text.setFont(QFont(FONT_FAMILY, 8))
                    galactic_text.setPos(10, scene_height - 20)
                    
                    # Add a small galactic position indicator
                    indicator_size = 60
                    indicator_x = sector_width - indicator_size - 10
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
        except Exception as e:
            logger.error(f"Error drawing sector map: {e}")
        
    def _on_search_requested(self, search_text):
        """Handle search requests from the sector view.
        
        Args:
            search_text: Text to search for in sector and system names
        """
        if not search_text or not hasattr(self, 'sectors_view_widget'):
            return
            
        # Search for sectors matching the text
        matching_sectors = self.sectors_db.search_sectors(search_text)
        
        # Search for systems matching the text
        matching_systems = self.sectors_db.search_systems(search_text)
        
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
                sector = self.sectors_db.get_sector_by_id(sector_id)
                if sector:
                    self.sectors_view_widget.set_sector(sector)
                    # Filter to show only matching systems in this sector
                    systems_in_sector = [s for s in matching_systems if s.get('sector_id') == sector_id]
                    self.sectors_view_widget.set_systems(systems_in_sector)
                    
    def _format_planet_details_text(self, system_data, planets):
        """Format planet details as plain text.
        
        Args:
            system_data: Dictionary containing system information
            planets: List of planet dictionaries
            
        Returns:
            Plain text string with formatted planet details
        """
        if not system_data:
            return "No system data available"
        
        system_name = system_data.get('name', UNKNOWN_SYSTEM)
        system_hex = system_data.get('hex', 'Unknown')
        system_uwp = system_data.get('uwp', 'Unknown')
        
        text = f"SYSTEM: {system_name}\n"
        text += f"HEX: {system_hex}\n"
        text += f"UWP: {system_uwp}\n"
        
        if planets:
            text += "\nPLANETS:\n"
            for planet in planets:
                planet_name = planet.get('name', 'Unknown')
                planet_type = planet.get('planet_type', 'Unknown')
                text += f"  {planet_name} ({planet_type})\n"
        else:
            text += "\nNo planets found for this system.\n"
        
        return text
