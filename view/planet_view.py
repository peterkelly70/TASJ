import logging
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from view.planet_map_widget import PlanetMapWidget

logger = logging.getLogger(__name__)

class PlanetView(QWidget):
    """View for displaying planet details and related missions."""
    
    # Signals
    mission_generation_requested = pyqtSignal(dict)
    mission_selected = pyqtSignal(dict)
    map_generation_requested = pyqtSignal(dict)  # Signal for map generation
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Planet View")
        self.current_planet = None
        self.missions = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Planet header
        self.planet_header = QLabel("Select a planet")
        self.planet_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(self.planet_header)
        
        # Create a splitter for the main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Planet details and map
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Planet details group
        planet_details_group = QGroupBox("Planet Details")
        planet_details_layout = QVBoxLayout(planet_details_group)
        
        self.planet_details = QTextEdit()
        self.planet_details.setReadOnly(True)
        planet_details_layout.addWidget(self.planet_details)
        
        left_layout.addWidget(planet_details_group)
        
        # Planet map group
        planet_map_group = QGroupBox("Planet Map")
        planet_map_layout = QVBoxLayout(planet_map_group)
        
        # Planet map widget
        self.planet_map = PlanetMapWidget()
        planet_map_layout.addWidget(self.planet_map)
        
        # Map controls
        map_controls_layout = QHBoxLayout()
        self.generate_map_button = QPushButton("Generate New Map")
        self.generate_map_button.clicked.connect(self._on_generate_map_clicked)
        map_controls_layout.addWidget(self.generate_map_button)
        planet_map_layout.addLayout(map_controls_layout)
        
        left_layout.addWidget(planet_map_group)
        splitter.addWidget(left_panel)
        
        # Right panel - Missions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Missions group
        missions_group = QGroupBox("Available Missions")
        missions_layout = QVBoxLayout(missions_group)
        
        # Mission list
        self.mission_list = QListWidget()
        self.mission_list.itemClicked.connect(self._on_mission_selected)
        missions_layout.addWidget(self.mission_list)
        
        # Generate missions button
        generate_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate New Missions")
        self.generate_button.clicked.connect(self._on_generate_clicked)
        generate_layout.addWidget(self.generate_button)
        missions_layout.addLayout(generate_layout)
        
        right_layout.addWidget(missions_group)
        splitter.addWidget(right_panel)
        
        # Set the default splitter sizes
        splitter.setSizes([500, 300])
        
        self.setLayout(main_layout)
    
    def set_planet(self, planet: Dict[str, Any]):
        """Set the current planet and update the UI."""
        self.current_planet = planet
        self._update_planet_display()
        
        # Update planet map
        self.planet_map.set_planet(planet)
        
        # Clear missions when changing planets
        self.missions = []
        self._update_mission_list()
    
    def _update_planet_display(self):
        """Update the planet details display."""
        if not self.current_planet:
            self.planet_header.setText("Select a planet")
            self.planet_details.setText("")
            return
        
        # Update header
        name = self.current_planet.get("name", "Unknown")
        uwp = self.current_planet.get("UWP", "")
        self.planet_header.setText(f"{name} ({uwp})")
        
        # Format planet details
        details = f"Name: {name}\n"
        details += f"UWP: {uwp}\n"
        
        # Add other planet details if available
        if "trade_codes" in self.current_planet:
            trade_codes = self.current_planet["trade_codes"]
            if trade_codes:
                details += f"Trade Codes: {', '.join(trade_codes)}\n"
        
        if "description" in self.current_planet:
            details += f"\nDescription:\n{self.current_planet['description']}\n"
        
        self.planet_details.setText(details)
    
    def set_missions(self, missions: List[Dict[str, Any]]):
        """Set the list of missions for the current planet."""
        self.missions = missions
        self._update_mission_list()
    
    def _update_mission_list(self):
        """Update the mission list widget."""
        self.mission_list.clear()
        
        if not self.missions:
            self.mission_list.addItem("No missions available")
            return
        
        for mission in self.missions:
            title = mission.get("title", "Untitled Mission")
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, mission)
            self.mission_list.addItem(item)
    
    def _on_mission_selected(self, item):
        """Handle mission selection."""
        mission = item.data(Qt.ItemDataRole.UserRole)
        if mission:
            self.mission_selected.emit(mission)
    
    def _on_generate_clicked(self):
        """Handle generate missions button click."""
        if not self.current_planet:
            QMessageBox.warning(self, "Warning", "Please select a planet first.")
            return
        
        # Emit signal to request mission generation
        self.mission_generation_requested.emit({
            "world": self.current_planet,
            "count": 3,  # Default to 3 missions
            "use_gpt": True  # Default to using GPT
        })
        
    def _on_generate_map_clicked(self):
        """Handle generate map button click."""
        if not self.current_planet:
            QMessageBox.warning(self, "Warning", "Please select a planet first.")
            return
        
        # Generate map using the planet map widget
        self.planet_map.generate_new_map()
        
        # Emit signal to request map generation and storage
        self.map_generation_requested.emit({
            "planet": self.current_planet
        })

