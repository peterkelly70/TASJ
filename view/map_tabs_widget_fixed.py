import logging
import math
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea, QSplitter,
    QLabel, QGroupBox, QListWidget, QListWidgetItem, QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap

from view.planet_map_widget import PlanetMapWidget
from view.system_map_widget import SystemMapWidget
from view.sector_map_widget import SectorMapWidget

# Set up file logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'map_tabs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
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
        
        # Create sector map widget
        self.sector_map_widget = SectorMapWidget(self)
        self.sector_map_widget.system_selected.connect(self._on_system_selected)
        self.sector_map_widget.map_error.connect(self._on_map_error)
        
        # Create system map widget
        self.system_map_widget = SystemMapWidget(self)
        self.system_map_widget.planet_selected.connect(self._on_planet_selected)
        self.system_map_widget.map_error.connect(self._on_map_error)
        
        # Create planet map widget
        self.planet_map_widget = PlanetMapWidget(self, self.db_path)
        self.planet_map_widget.map_error.connect(self._on_map_error)
        
        # Add tabs
        self.map_tabs.addTab(self.sector_map_widget, TAB_SECTOR_MAP)
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
        
    def set_sector(self, sector, milieu=None):
        """Set the current sector.
        
        Args:
            sector: Dictionary containing sector data
            milieu: Optional milieu code to use for sector data
        """
        self.current_sector = sector
        
        # Update sector info in the info tab
        self._update_sector_info(sector)
        
        # Set sector in the sector map widget
        self.sector_map_widget.set_sector(sector, milieu)
        
        # Switch to sector map tab
        self.map_tabs.setCurrentIndex(0)
        self._clear_status_message()
        
    def _on_system_selected(self, system_data):
        """Handle system selection from sector map."""
        logger.info("\n=== System Selection Started ===")
        logger.debug(f"System data type: {type(system_data)}")
        logger.debug(f"System data: {system_data}")
        
        if not system_data:
            logger.error("No system data provided")
            return
            
        try:
            # Store current system
            self.current_system = system_data
            logger.info(f"System stored: {system_data.get('name')} (ID: {system_data.get('id')})")
            
            # Log current tab states
            logger.debug(f"Current map tab index: {self.map_tabs.currentIndex()}")
            logger.debug(f"Current info tab index: {self.info_tabs.currentIndex()}")
            logger.debug(f"Map tab count: {self.map_tabs.count()}")
            logger.debug(f"Info tab count: {self.info_tabs.count()}")
            
            # Log tab names for debugging
            for i in range(self.map_tabs.count()):
                logger.debug(f"Map tab {i}: {self.map_tabs.tabText(i)}")
            for i in range(self.info_tabs.count()):
                logger.debug(f"Info tab {i}: {self.info_tabs.tabText(i)}")
            
            # Switch to system map tab first to ensure widgets are initialized
            logger.debug("Switching to system map tab...")
            self.map_tabs.setCurrentIndex(1)  # System map tab
            logger.debug(f"Map tab after switch: {self.map_tabs.currentIndex()}")
            
            # Get planets for this system
            logger.debug("Fetching planets...")
            from model.system_db import SystemDB
            system_db = SystemDB()
            system_id = system_data.get("id")
            logger.debug(f"Fetching planets for system ID: {system_id}")
            planets = system_db.get_planets_by_system_id(system_id)
            logger.debug(f"Found {len(planets) if planets else 0} planets")
            
            # Set system in system map widget
            logger.debug("Updating system map widget...")
            self.system_map_widget.set_system(system_data, planets)
            
            # Update system info
            logger.debug("Updating system info...")
            self._update_system_info(system_data)
            
            # Switch to system info tab
            logger.debug("Switching to system info tab...")
            self.info_tabs.setCurrentIndex(1)  # System info tab
            current_info_widget = self.info_tabs.currentWidget()
            logger.debug(f"Current info widget: {current_info_widget}")
            
            if current_info_widget:
                current_info_widget.show()
                current_info_widget.update()
                logger.debug("Info tab updated")
            else:
                logger.warning("Could not get current info widget")
            
            # Force update the UI
            self.info_tabs.update()
            logger.debug("UI update complete")
            
            # Forward the signal
            logger.debug("Emitting system_selected signal...")
            self.system_selected.emit(system_data)
            logger.info("=== System Selection Completed Successfully ===\n")
            
        except Exception as e:
            logger.error(f"Error in _on_system_selected: {str(e)}", exc_info=True)
            logger.info("=== System Selection Failed ===\n")
        
    def _on_planet_selected(self, planet_data):
        """Handle planet selection from system map."""
        if not planet_data:
            return
            
        # Set planet in planet map widget
        self.planet_map_widget.set_planet(planet_data)
        
        # Switch to planet map tab
        self.map_tabs.setCurrentIndex(2)  # Fixed: use map_tabs instead of tab_widget
        self._clear_status_message()
        
        # Forward the signal
        self.planet_selected.emit(planet_data)
        
    def _on_map_error(self, error_message):
        """Handle map error messages from any map widget."""
        if self.status_bar:
            self.status_bar.showMessage(f"Error: {error_message}", 10000)  # Show for 10 seconds
            
    def _clear_status_message(self):
        """Clear any status message."""
        if self.status_bar:
            self.status_bar.clearMessage()
            
    def _update_system_info(self, system, loading_message=None):
        """Update the system info tab with system details and planet list.
        
        Args:
            system: Dictionary containing system data
            loading_message: Optional loading message to display
        """
        logger.debug("\n--- Updating System Info ---")
        logger.debug(f"System data: {system}")
        logger.debug(f"Loading message: {loading_message}")
        
        try:
            # Clear previous content
            logger.debug("Clearing previous content...")
            while self.system_info_layout.count():
                item = self.system_info_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            if loading_message:
                # Show loading message
                logger.debug("Showing loading message")
                label = QLabel(loading_message)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.system_info_layout.addWidget(label)
                self.system_info_layout.update()
                logger.debug("Loading message displayed")
                return
                
            if not system:
                logger.debug("No system data provided, showing placeholder")
                label = QLabel("No system selected")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.system_info_layout.addWidget(label)
                return
            
        if not system:
            # No system selected
            label = QLabel("No system selected")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.system_info_layout.addWidget(label)
            return
            
        # Create a scroll area for the system info
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create a widget to hold the content
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # System details group
        details_group = QGroupBox("System Details")
        details_layout = QVBoxLayout(details_group)
        
        # Add system information
        if 'name' in system:
            name_label = QLabel(f"<b>Name:</b> {system['name']}")
            details_layout.addWidget(name_label)
            
        if 'hex_code' in system:
            hex_label = QLabel(f"<b>Hex:</b> {system['hex_code']}")
            details_layout.addWidget(hex_label)
            
        if 'uwp' in system:
            uwp_label = QLabel(f"<b>UWP:</b> {system['uwp']}")
            details_layout.addWidget(uwp_label)
            
        if 'trade_codes' in system and system['trade_codes']:
            codes = ', '.join(system['trade_codes'])
            codes_label = QLabel(f"<b>Trade Codes:</b> {codes}")
            codes_label.setWordWrap(True)
            details_layout.addWidget(codes_label)
            
        if 'bases' in system and system['bases']:
            bases_label = QLabel(f"<b>Bases:</b> {system['bases']}")
            details_layout.addWidget(bases_label)
            
        if 'zone' in system and system['zone']:
            zone_label = QLabel(f"<b>Zone:</b> {system['zone']}")
            details_layout.addWidget(zone_label)
            
        if 'pbg' in system:
            pbg_label = QLabel(f"<b>PBG:</b> {system['pbg']}")
            details_layout.addWidget(pbg_label)
            
        if 'allegiance' in system and system['allegiance']:
            alleg_label = QLabel(f"<b>Allegiance:</b> {system['allegiance']}")
            details_layout.addWidget(alleg_label)
            
        if 'stellar' in system and system['stellar']:
            stellar_label = QLabel(f"<b>Stellar:</b> {system['stellar']}")
            stellar_label.setWordWrap(True)
            details_layout.addWidget(stellar_label)
            
        layout.addWidget(details_group)
        
        # Add planets list if available
        if hasattr(self, 'system_map_widget') and hasattr(self.system_map_widget, 'planets'):
            planets = self.system_map_widget.planets
            if planets:
                planets_group = QGroupBox("Planets")
                planets_layout = QVBoxLayout(planets_group)
                
                planet_list = QListWidget()
                for planet in planets:
                    item_text = f"{planet.get('orbit', '?')}. {planet.get('name', 'Unnamed')}"
                    if 'uwp' in planet:
                        item_text += f" - {planet['uwp']}"
                    if 'trade_codes' in planet and planet['trade_codes']:
                        item_text += f" ({', '.join(planet['trade_codes'])})"
                        
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, planet)
                    planet_list.addItem(item)
                
                # Connect planet selection
                planet_list.itemClicked.connect(
                    lambda item: self._on_planet_selected(item.data(Qt.ItemDataRole.UserRole)))
                
                planets_layout.addWidget(planet_list)
                layout.addWidget(planets_group)
        
        # Add a stretch to push everything to the top
        layout.addStretch(1)
        
        # Set up the scroll area
        scroll.setWidget(content)
        self.system_info_layout.addWidget(scroll)
    
    def _on_tab_changed(self, index):
        """Handle tab change events."""
        # This can be used to update content when switching tabs
        pass
        
    def _update_sector_info(self, sector):
        """Update the sector info tab with sector details.
        
        Args:
            sector: Dictionary containing sector data
        """
        # Clear previous content
        while self.sector_info_layout.count():
            item = self.sector_info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
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
