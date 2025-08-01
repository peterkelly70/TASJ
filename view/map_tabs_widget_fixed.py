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
from view.sector_map_widget import SectorMapWidget

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
        if not system_data:
            return
            
        # Get planets for this system
        from model.system_db import SystemDB
        system_db = SystemDB()
        planets = system_db.get_planets_by_system_id(system_data.get("id"))
        
        # Set system in system map widget
        self.system_map_widget.set_system(system_data, planets)
        
        # Switch to system map tab
        self.map_tabs.setCurrentIndex(1)  # Fixed: use map_tabs instead of tab_widget
        self._clear_status_message()
        
        # Forward the signal
        self.system_selected.emit(system_data)
        
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
