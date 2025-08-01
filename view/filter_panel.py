import logging
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)

class FilterPanel(QWidget):
    """Panel for filtering sectors, systems, and planets."""
    
    filter_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sectors = []
        self.systems = []
        self.planets = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create filter form
        filter_group = QGroupBox("Database Filters")
        form_layout = QFormLayout()
        
        # Sector filter
        self.sector_combo = QComboBox()
        self.sector_combo.setEditable(True)
        self.sector_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.sector_combo.currentIndexChanged.connect(self._on_sector_changed)
        form_layout.addRow("Sector:", self.sector_combo)
        
        # System filter
        self.system_combo = QComboBox()
        self.system_combo.setEditable(True)
        self.system_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.system_combo.currentIndexChanged.connect(self._on_system_changed)
        form_layout.addRow("System:", self.system_combo)
        
        # Planet filter
        self.planet_combo = QComboBox()
        self.planet_combo.setEditable(True)
        self.planet_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.planet_combo.currentIndexChanged.connect(self._on_planet_changed)
        form_layout.addRow("Planet:", self.planet_combo)
        
        # Apply filter button
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply Filter")
        self.apply_button.clicked.connect(self._on_apply_filter)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._on_reset_filter)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        
        filter_group.setLayout(form_layout)
        main_layout.addWidget(filter_group)
        main_layout.addLayout(button_layout)
        
        # Add stretch to push everything to the top
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
        
    def set_sectors(self, sectors: List[Dict[str, Any]]):
        """Set the list of sectors for filtering."""
        self.sectors = sectors
        self.sector_combo.clear()
        self.sector_combo.addItem("All Sectors", None)
        
        for sector in sectors:
            self.sector_combo.addItem(sector.get("name", "Unknown"), sector.get("id"))
            
    def set_systems(self, systems: List[Dict[str, Any]]):
        """Set the list of systems for filtering."""
        self.systems = systems
        self.system_combo.clear()
        self.system_combo.addItem("All Systems", None)
        
        for system in systems:
            self.system_combo.addItem(system.get("name", "Unknown"), system.get("id"))
            
    def set_planets(self, planets: List[Dict[str, Any]]):
        """Set the list of planets for filtering."""
        self.planets = planets
        self.planet_combo.clear()
        self.planet_combo.addItem("All Planets", None)
        
        for planet in planets:
            self.planet_combo.addItem(planet.get("name", "Unknown"), planet.get("id"))
            
    def _on_sector_changed(self, index):
        """Handle sector selection change."""
        # Update systems based on selected sector
        if index > 0:  # Not "All Sectors"
            sector_id = self.sector_combo.itemData(index)
            # Filter systems by sector_id
            filtered_systems = [s for s in self.systems if s.get("sector_id") == sector_id]
            self.set_systems(filtered_systems)
        
    def _on_system_changed(self, index):
        """Handle system selection change."""
        # Update planets based on selected system
        if index > 0:  # Not "All Systems"
            system_id = self.system_combo.itemData(index)
            # Filter planets by system_id
            filtered_planets = [p for p in self.planets if p.get("system_id") == system_id]
            self.set_planets(filtered_planets)
        
    def _on_planet_changed(self, index):
        """Handle planet selection change."""
        # Nothing to update when planet changes
        pass
        
    def _on_apply_filter(self):
        """Apply the current filter settings."""
        filter_data = {
            "sector_id": self.sector_combo.currentData(),
            "system_id": self.system_combo.currentData(),
            "planet_id": self.planet_combo.currentData()
        }
        self.filter_changed.emit(filter_data)
        
    def _on_reset_filter(self):
        """Reset all filters."""
        self.sector_combo.setCurrentIndex(0)
        self.system_combo.setCurrentIndex(0)
        self.planet_combo.setCurrentIndex(0)
        
        # Emit empty filter
        self.filter_changed.emit({})
