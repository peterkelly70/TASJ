"""
Mission Detail View for Traveller RPG campaigns.

This module provides a UI for viewing detailed mission information including
particulars, NPCs, maps, and other mission-specific content.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QGroupBox, QTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

logger = logging.getLogger(__name__)

class MissionDetailView(QWidget):
    """View for displaying detailed mission information."""
    
    # Signals
    mission_closed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the mission detail view."""
        super().__init__(parent)
        self.setWindowTitle("Mission Details")
        self.current_mission = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Mission header
        self.mission_header = QLabel("Mission Details")
        self.mission_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(self.mission_header)
        
        # Tab widget for different mission aspects
        self.tab_widget = QTabWidget()
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # Mission description
        description_group = QGroupBox("Description")
        description_layout = QVBoxLayout(description_group)
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        description_layout.addWidget(self.description_text)
        overview_layout.addWidget(description_group)
        
        # Mission structure
        structure_group = QGroupBox("Structure")
        structure_layout = QVBoxLayout(structure_group)
        self.structure_text = QTextEdit()
        self.structure_text.setReadOnly(True)
        structure_layout.addWidget(self.structure_text)
        overview_layout.addWidget(structure_group)
        
        self.tab_widget.addTab(overview_tab, "Overview")
        
        # NPCs tab
        npcs_tab = QWidget()
        npcs_layout = QVBoxLayout(npcs_tab)
        
        self.npcs_text = QTextEdit()
        self.npcs_text.setReadOnly(True)
        npcs_layout.addWidget(self.npcs_text)
        
        self.tab_widget.addTab(npcs_tab, "NPCs")
        
        # Map tab
        map_tab = QWidget()
        map_layout = QVBoxLayout(map_tab)
        
        # Map description
        map_desc_group = QGroupBox("Map Description")
        map_desc_layout = QVBoxLayout(map_desc_group)
        self.map_description = QTextEdit()
        self.map_description.setReadOnly(True)
        map_desc_layout.addWidget(self.map_description)
        map_layout.addWidget(map_desc_group)
        
        # Map image
        map_image_group = QGroupBox("Map")
        map_image_layout = QVBoxLayout(map_image_group)
        
        # Scroll area for the map
        map_scroll = QScrollArea()
        map_scroll.setWidgetResizable(True)
        map_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        map_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container for the map image
        map_container = QWidget()
        map_container_layout = QVBoxLayout(map_container)
        
        self.map_label = QLabel("No map available")
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        map_container_layout.addWidget(self.map_label)
        
        map_scroll.setWidget(map_container)
        map_image_layout.addWidget(map_scroll)
        map_layout.addWidget(map_image_group)
        
        self.tab_widget.addTab(map_tab, "Map")
        
        # Particulars tab
        particulars_tab = QWidget()
        particulars_layout = QVBoxLayout(particulars_tab)
        
        self.particulars_text = QTextEdit()
        self.particulars_text.setReadOnly(True)
        particulars_layout.addWidget(self.particulars_text)
        
        self.tab_widget.addTab(particulars_tab, "Particulars")
        
        main_layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self._on_close_clicked)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.resize(800, 600)
    
    def set_mission(self, mission):
        """Set the mission to display."""
        # Convert Mission object to dict if needed
        if hasattr(mission, 'to_dict') and callable(mission.to_dict):
            self.current_mission = mission.to_dict()
        elif hasattr(mission, '__dict__'):
            # It's a Mission object without to_dict method
            mission_dict = mission.__dict__.copy()
            # Handle nested objects like particulars
            if hasattr(mission, 'particulars') and hasattr(mission.particulars, '__dict__'):
                mission_dict['particulars'] = mission.particulars.__dict__.copy()
            self.current_mission = mission_dict
        else:
            # It's already a dict
            self.current_mission = mission
            
        self._update_mission_display()
    
    def _update_mission_display(self):
        """Update the mission display with current mission data."""
        if not self.current_mission:
            self.mission_header.setText("No Mission Selected")
            return
        
        # Update header
        title = self.current_mission.get("title", "Untitled Mission")
        self.mission_header.setText(title)
        self.setWindowTitle(f"Mission: {title}")
        
        # Update description
        description = self.current_mission.get("description", "No description available.")
        self.description_text.setText(description)
        
        # Update structure
        structure = self.current_mission.get("structure", {})
        structure_text = self._format_mission_structure(structure)
        self.structure_text.setText(structure_text)
        
        # Update map description
        map_description = self.current_mission.get("map_description", "No map description available.")
        self.map_description.setText(map_description)
        
        # Update map image
        map_image = self.current_mission.get("map_image")
        if map_image:
            try:
                pixmap = QPixmap()
                pixmap.loadFromData(map_image)
                self.map_label.setPixmap(pixmap)
                self.map_label.setScaledContents(True)
            except Exception as e:
                logger.error(f"Error loading map image: {e}")
                self.map_label.setText("Error loading map image")
        else:
            self.map_label.setText("No map available")
            self.map_label.setPixmap(QPixmap())
        
        # Update NPCs
        npcs = self.current_mission.get("npcs", [])
        npcs_text = self._format_npcs(npcs)
        self.npcs_text.setText(npcs_text)
        
        # Update particulars
        particulars = self.current_mission.get("particulars", {})
        particulars_text = self._format_particulars(particulars)
        self.particulars_text.setText(particulars_text)
    
    def _format_mission_structure(self, structure: Dict[str, Any]) -> str:
        """Format the mission structure as readable text."""
        if not structure:
            return "No structure information available."
        
        text = ""
        
        # Scenario type
        scenario_type = structure.get("scenario_type", {})
        if scenario_type:
            text += f"Scenario Type: {scenario_type.get('name', 'Unknown')}\n\n"
        
        # Details
        details = structure.get("details", {})
        if details:
            text += "Details:\n"
            for table_name, detail in details.items():
                text += f"- {table_name}: {detail.get('name', 'Unknown')}\n"
            text += "\n"
        
        # References
        references = structure.get("references", [])
        if references:
            text += "Reference Chain:\n"
            for ref in references:
                phase = ref.get("phase", "Unknown")
                table_id = ref.get("table_id", "Unknown")
                result = ref.get("result", "Unknown")
                text += f"- {phase}, Table {table_id}: {result}\n"
        
        return text
    
    def _format_npcs(self, npcs) -> str:
        """Format NPCs as readable text."""
        if not npcs:
            return "No NPCs available for this mission."
        
        text = ""
        
        for i, npc in enumerate(npcs):
            if isinstance(npc, dict):
                name = npc.get("name", f"NPC {i+1}")
                role = npc.get("role", "Unknown role")
                description = npc.get("description", "No description available.")
                
                text += f"## {name} ({role})\n\n"
                text += f"{description}\n\n"
                
                # Add other NPC details if available
                stats = npc.get("stats", {})
                if stats:
                    text += "Stats:\n"
                    for stat_name, stat_value in stats.items():
                        text += f"- {stat_name}: {stat_value}\n"
                    text += "\n"
            else:
                text += f"NPC {i+1}: {npc}\n\n"
        
        return text
    
    def _format_particulars(self, particulars) -> str:
        """Format mission particulars as readable text."""
        if not particulars:
            return "No particulars available for this mission."
        
        # Handle particulars as dict or object
        if isinstance(particulars, dict):
            return self._format_particulars_dict(particulars)
        else:
            return self._format_particulars_object(particulars)
    
    def _format_particulars_dict(self, particulars: Dict[str, Any]) -> str:
        """Format particulars from a dictionary."""
        text = ""
        
        # Content (main particulars text)
        content = particulars.get("content", "")
        if content:
            text += f"{content}\n\n"
        
        # Complications
        complications = particulars.get("complications", "")
        if complications:
            text += f"Complications:\n{complications}\n\n"
        
        # Other particulars fields
        for key, value in particulars.items():
            if key not in ["content", "complications"] and value:
                text += f"{key.capitalize()}:\n{value}\n\n"
        
        return text
    
    def _format_particulars_object(self, particulars) -> str:
        """Format particulars from an object."""
        try:
            text = ""
            
            # Content (main particulars text)
            if hasattr(particulars, "content") and particulars.content:
                text += f"{particulars.content}\n\n"
            
            # Complications
            if hasattr(particulars, "complications") and particulars.complications:
                text += f"Complications:\n{particulars.complications}\n\n"
            
            return text
        except Exception as e:
            logger.error(f"Error formatting particulars: {e}")
            return "Error formatting mission particulars."
    
    def _on_close_clicked(self):
        """Handle close button click."""
        self.mission_closed.emit()
        self.close()
