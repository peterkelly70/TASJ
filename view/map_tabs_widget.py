import logging
import math
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea, QSplitter,
    QLabel, QGroupBox, QListWidget, QListWidgetItem, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap

from view.planet_map_widget import PlanetMapWidget
from view.system_map_widget import SystemMapWidget
# Replace SectorMapWidget with HexMapWidget
from view.hex_map_widget import HexMapWidget

logger = logging.getLogger(__name__)

# Constants for tab names
TAB_SECTOR_MAP = "Sector Map"
TAB_SYSTEM_MAP = "System Map"
TAB_PLANET_MAP = "Planet Map"
TAB_SECTOR_INFO = "Sector Info"
TAB_SYSTEM_INFO = "System Info"
TAB_PLANET_INFO = "Planet Info"

# Define MapTabsWidget class
class MapTabsWidget(QWidget):
    """Widget for displaying map tabs (sector, system, planet)."""
    
    system_selected = pyqtSignal(dict)
    planet_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.db_path = db_path
        self.status_bar = None
        self.current_sector = None
        self.current_system = None
        self.current_planet = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins for more space
        
        # Create a vertical splitter for map and info areas
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setChildrenCollapsible(False)  # Prevent panels from being collapsed
        
        # Map area (top)
        self.map_area = QWidget()
        map_layout = QVBoxLayout(self.map_area)
        map_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        
        # Create map tabs widget
        self.map_tabs = QTabWidget(self)
        
        # Create hex map widget (replacing SectorMapWidget)
        self.hex_map_widget = HexMapWidget(self)
        self.hex_map_widget.system_selected.connect(self._on_system_selected)
        self.hex_map_widget.system_updated.connect(self._on_system_updated)
        self.hex_map_widget.system_deleted.connect(self._on_system_deleted)
        self.hex_map_widget.map_error.connect(self._on_map_error)
        
        # Create system map widget
        self.system_map_widget = SystemMapWidget(self)
        self.system_map_widget.planet_selected.connect(self._on_planet_selected)
        self.system_map_widget.map_error.connect(self._on_map_error)
        
        # Create planet map widget
        self.planet_map_widget = PlanetMapWidget(self, self.db_path)
        self.planet_map_widget.map_error.connect(self._on_map_error)
        
        # Add tabs
        self.map_tabs.addTab(self.hex_map_widget, TAB_SECTOR_MAP)
        self.map_tabs.addTab(self.system_map_widget, TAB_SYSTEM_MAP)
        self.map_tabs.addTab(self.planet_map_widget, TAB_PLANET_MAP)
        
        map_layout.addWidget(self.map_tabs)
        self.main_splitter.addWidget(self.map_area)
        
        # Info area (bottom) with tabs for sector, system, planet info
        self.info_area = QWidget()
        info_layout = QVBoxLayout(self.info_area)
        info_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        
        # Create info tabs widget
        self.info_tabs = QTabWidget(self)
        
        # Create tab content widgets
        self.sector_info_widget = QScrollArea()
        self.sector_info_widget.setWidgetResizable(True)
        self.sector_info_content = QWidget()
        self.sector_info_layout = QVBoxLayout(self.sector_info_content)
        self.sector_info_widget.setWidget(self.sector_info_content)
        
        self.system_info_widget = QScrollArea()
        self.system_info_widget.setWidgetResizable(True)
        self.system_info_content = QWidget()
        self.system_info_layout = QVBoxLayout(self.system_info_content)
        self.system_info_widget.setWidget(self.system_info_content)
        
        self.planet_info_widget = QScrollArea()
        self.planet_info_widget.setWidgetResizable(True)
        self.planet_info_content = QWidget()
        self.planet_info_layout = QVBoxLayout(self.planet_info_content)
        self.planet_info_widget.setWidget(self.planet_info_content)
        
        # Add tabs to info tabs widget
        self.info_tabs.addTab(self.sector_info_widget, TAB_SECTOR_INFO)
        self.info_tabs.addTab(self.system_info_widget, TAB_SYSTEM_INFO)
        self.info_tabs.addTab(self.planet_info_widget, TAB_PLANET_INFO)
        
        info_layout.addWidget(self.info_tabs)
        self.main_splitter.addWidget(self.info_area)
        
        # Set initial splitter sizes (70% map, 30% info)
        self.main_splitter.setSizes([700, 300])
        
        # Add splitter to main layout
        layout.addWidget(self.main_splitter)
        
        # Connect tab change signals
        self.map_tabs.currentChanged.connect(self._on_tab_changed)
        self.info_tabs.currentChanged.connect(self._on_tab_changed)
        
    def set_db_path(self, db_path):
        """Set the database path for the planet map widget."""
        self.db_path = db_path
        self.planet_map_widget.set_db_path(db_path)
        
    def set_sector(self, sector, systems=None, milieu=None):
        """Set the current sector.
        
        Args:
            sector: Dictionary containing sector data
            systems: Optional list of systems in the sector
            milieu: Optional milieu code to use for sector data
        """
        self.current_sector = sector
        
        if not sector:
            # Clear the hex map
            self.hex_map_widget.set_systems([])
            self._update_sector_info(None)
            return
            
        # Set sector in hex map widget
        self.hex_map_widget.set_sector(sector, milieu)
        
        # Set systems if provided
        if systems is not None:
            self.hex_map_widget.set_systems(systems)
        
        # Update sector info tab
        self._update_sector_info(sector)
        
        # Switch to sector map tab
        self.map_tabs.setCurrentWidget(self.hex_map_widget)
        
    def _on_system_selected(self, system_data):
        """Handle system selection from hex map."""
        self.current_system = system_data
        self.system_selected.emit(system_data)
        self._update_system_info(system_data)
        
        # Switch to system map tab and update it
        self.map_tabs.setCurrentWidget(self.system_map_widget)
        self.system_map_widget.set_system(system_data)
        
    def _on_system_updated(self, system_data):
        """Handle system update from hex map."""
        # TODO: Implement system update handling
        logger.info(f"System updated: {system_data.get('name', 'Unknown')}")
        
    def _on_system_deleted(self, system_data):
        """Handle system deletion from hex map."""
        # TODO: Implement system deletion handling
        logger.info(f"System deleted: {system_data.get('name', 'Unknown')}")
        
    def _on_planet_selected(self, planet_data):
        """Handle planet selection from system map."""
        self.current_planet = planet_data
        self.planet_selected.emit(planet_data)
        self._update_planet_info(planet_data)
        
        # Switch to planet map tab and update it
        self.map_tabs.setCurrentWidget(self.planet_map_widget)
        self.planet_map_widget.set_planet(planet_data)
        
    def _on_map_error(self, error_message):
        """Handle map error messages from any map widget."""
        if self.status_bar:
            self.status_bar.showMessage(f"Error: {error_message}", 10000)  # Show for 10 seconds
            
    def _clear_status_message(self):
        """Clear any status message."""
        if self.status_bar:
            self.status_bar.clearMessage()
            
    def _on_tab_changed(self, index):
        """Handle tab change events."""
        # This can be used to update content when switching tabs
        pass
        
    def _update_planet_info(self, planet, loading_message=None):
        """Update the planet info tab with planet details.
        
        Args:
            planet: Dictionary containing planet data
            loading_message: Optional loading message to display
        """
        # Clear previous content
        while self.planet_info_layout.count():
            item = self.planet_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if loading_message:
            # Show loading message
            label = QLabel(loading_message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.planet_info_layout.addWidget(label)
            return
                
        if not planet:
            # No planet selected
            label = QLabel("No planet selected")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.planet_info_layout.addWidget(label)
            return
            
        # Create a group box for planet details
        details_group = QGroupBox("Planet Details")
        details_layout = QVBoxLayout(details_group)
        
        # Add planet information
        if 'name' in planet:
            name_label = QLabel(f"<b>Name:</b> {planet['name']}")
            details_layout.addWidget(name_label)
            
        if 'uwp' in planet:
            uwp_label = QLabel(f"<b>UWP:</b> {planet['uwp']}")
            details_layout.addWidget(uwp_label)
            
        if 'starport' in planet:
            starport_label = QLabel(f"<b>Starport:</b> {planet['starport']}")
            details_layout.addWidget(starport_label)
            
        if 'size' in planet:
            size_label = QLabel(f"<b>Size:</b> {planet['size']}")
            details_layout.addWidget(size_label)
            
        if 'atmosphere' in planet:
            atmo_label = QLabel(f"<b>Atmosphere:</b> {planet['atmosphere']}")
            details_layout.addWidget(atmo_label)
            
        if 'hydrographics' in planet:
            hydro_label = QLabel(f"<b>Hydrographics:</b> {planet['hydrographics']}")
            details_layout.addWidget(hydro_label)
            
        if 'population' in planet:
            pop_label = QLabel(f"<b>Population:</b> {planet['population']}")
            details_layout.addWidget(pop_label)
            
        if 'government' in planet:
            gov_label = QLabel(f"<b>Government:</b> {planet['government']}")
            details_layout.addWidget(gov_label)
            
        if 'law_level' in planet:
            law_label = QLabel(f"<b>Law Level:</b> {planet['law_level']}")
            details_layout.addWidget(law_label)
            
        if 'tech_level' in planet:
            tech_label = QLabel(f"<b>Tech Level:</b> {planet['tech_level']}")
            details_layout.addWidget(tech_label)
            
        # Add a spacer at the bottom
        self.planet_info_layout.addWidget(details_group)
        self.planet_info_layout.addStretch(1)
        
    def _update_system_info(self, system, loading_message=None):
        """Update the system info tab with system details.
        
        Args:
            system: Dictionary containing system data
            loading_message: Optional loading message to display
        """
        # Clear previous content
        while self.system_info_layout.count():
            item = self.system_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if loading_message:
            # Show loading message
            label = QLabel(loading_message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.system_info_layout.addWidget(label)
            return
                
        if not system:
            # No system selected
            label = QLabel("No system selected")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.system_info_layout.addWidget(label)
            return
            
        # Create a group box for system details
        details_group = QGroupBox("System Details")
        details_layout = QVBoxLayout(details_group)
        
        # Add system information
        if 'name' in system:
            name_label = QLabel(f"<b>Name:</b> {system['name']}")
            details_layout.addWidget(name_label)
            
        if 'sector_name' in system:
            sector_label = QLabel(f"<b>Sector:</b> {system['sector_name']}")
            details_layout.addWidget(sector_label)
            
        if 'hex' in system:
            hex_label = QLabel(f"<b>Hex:</b> {system['hex']}")
            details_layout.addWidget(hex_label)
            
        if 'uwp' in system:
            uwp_label = QLabel(f"<b>UWP:</b> {system['uwp']}")
            details_layout.addWidget(uwp_label)
            
        if 'bases' in system and system['bases']:
            bases_label = QLabel(f"<b>Bases:</b> {system['bases']}")
            details_layout.addWidget(bases_label)
            
        if 'zone' in system and system['zone']:
            zone_label = QLabel(f"<b>Zone:</b> {system['zone']}")
            details_layout.addWidget(zone_label)
            
        if 'allegiance' in system and system['allegiance']:
            allegiance_label = QLabel(f"<b>Allegiance:</b> {system['allegiance']}")
            details_layout.addWidget(allegiance_label)
            
        # Add a spacer at the bottom
        self.system_info_layout.addWidget(details_group)
        self.system_info_layout.addStretch(1)
        
    def _update_sector_info(self, sector, loading_message=None):
        """Update the sector info tab with sector details.
        
        Args:
            sector: Dictionary containing sector data
            loading_message: Optional loading message to display
        """
        # Clear previous content
        while self.sector_info_layout.count():
            item = self.sector_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if loading_message:
            # Show loading message
            label = QLabel(loading_message)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sector_info_layout.addWidget(label)
            return
                
        if not sector:
            # No sector selected
            label = QLabel("No sector selected")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sector_info_layout.addWidget(label)
            return
            
        # Create a group box for sector details
        details_group = QGroupBox("Sector Details")
        details_layout = QVBoxLayout(details_group)
        
        # Add sector information
        if 'name' in sector:
            name_label = QLabel(f"<b>Name:</b> {sector['name']}")
            details_layout.addWidget(name_label)
            
        if 'abbreviation' in sector:
            abbr_label = QLabel(f"<b>Abbreviation:</b> {sector['abbreviation']}")
            details_layout.addWidget(abbr_label)
            
        if 'milieu' in sector:
            milieu_label = QLabel(f"<b>Milieu:</b> {sector['milieu']}")
            details_layout.addWidget(milieu_label)
            
        if 'x' in sector and 'y' in sector:
            coords_label = QLabel(f"<b>Coordinates:</b> ({sector['x']}, {sector['y']})")
            details_layout.addWidget(coords_label)
            
        if 'tags' in sector and sector['tags']:
            tags_label = QLabel(f"<b>Tags:</b> {', '.join(sector['tags'])}")
            tags_label.setWordWrap(True)
            details_layout.addWidget(tags_label)
            
        # Add a spacer at the bottom
        self.sector_info_layout.addWidget(details_group)
        self.sector_info_layout.addStretch(1)
