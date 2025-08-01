"""
Mission Generator View for Traveller RPG campaigns.

This module provides a UI for generating, viewing, and editing missions for planets/systems.
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSpinBox, QTextEdit, QCheckBox, QTabWidget,
    QGroupBox, QScrollArea, QSplitter, QLineEdit, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)

class MissionGeneratorView(QWidget):
    """View for generating, viewing, and editing missions."""
    
    # Signals
    mission_generated = pyqtSignal(dict)
    mission_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the mission generator view."""
        super().__init__(parent)
        self.setWindowTitle("Mission Generator")
        self.missions = []
        self.current_mission = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create a splitter for the main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls and mission list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Controls group
        controls_group = QGroupBox("Generate Missions")
        controls_layout = QVBoxLayout(controls_group)
        
        # World selection
        world_layout = QHBoxLayout()
        world_layout.addWidget(QLabel("World:"))
        self.world_combo = QComboBox()
        world_layout.addWidget(self.world_combo)
        controls_layout.addLayout(world_layout)
        
        # Number of missions
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Number of Missions:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10)
        self.count_spin.setValue(3)
        count_layout.addWidget(self.count_spin)
        controls_layout.addLayout(count_layout)
        
        # Use GPT checkbox
        self.use_gpt_check = QCheckBox("Enhance with AI")
        self.use_gpt_check.setChecked(True)
        controls_layout.addWidget(self.use_gpt_check)
        
        # Generate button
        self.generate_button = QPushButton("Generate Missions")
        controls_layout.addWidget(self.generate_button)
        
        left_layout.addWidget(controls_group)
        
        # Mission list group
        mission_list_group = QGroupBox("Mission List")
        mission_list_layout = QVBoxLayout(mission_list_group)
        
        self.mission_list = QListWidget()
        mission_list_layout.addWidget(self.mission_list)
        
        left_layout.addWidget(mission_list_group)
        
        # Right panel - Mission details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Mission title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        right_layout.addLayout(title_layout)
        
        # Mission details tabs
        self.detail_tabs = QTabWidget()
        
        # Description tab
        description_tab = QWidget()
        description_layout = QVBoxLayout(description_tab)
        self.description_edit = QTextEdit()
        description_layout.addWidget(self.description_edit)
        self.detail_tabs.addTab(description_tab, "Description")
        
        # Map tab
        map_tab = QWidget()
        map_layout = QVBoxLayout(map_tab)
        self.map_description_edit = QTextEdit()
        map_layout.addWidget(QLabel("Map Description:"))
        map_layout.addWidget(self.map_description_edit)
        self.detail_tabs.addTab(map_tab, "Map")
        
        # Structure tab
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        self.structure_text = QTextEdit()
        self.structure_text.setReadOnly(True)
        structure_layout.addWidget(self.structure_text)
        self.detail_tabs.addTab(structure_tab, "Structure")
        
        right_layout.addWidget(self.detail_tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Mission")
        self.export_button = QPushButton("Export Map")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)
        right_layout.addLayout(button_layout)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])  # Set initial sizes
        
        # Connect signals
        self.generate_button.clicked.connect(self._on_generate_clicked)
        self.mission_list.currentItemChanged.connect(self._on_mission_selected)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)
    
    def set_worlds(self, worlds: List[Dict[str, Any]]):
        """
        Set the available worlds in the combo box.
        
        Args:
            worlds: List of world dicts with at least 'name' and 'UWP' keys
        """
        self.world_combo.clear()
        for world in worlds:
            self.world_combo.addItem(f"{world['name']} ({world['UWP']})", world)
    
    def get_selected_world(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected world.
        
        Returns:
            The selected world dict or None if none selected
        """
        if self.world_combo.count() == 0:
            return None
        
        return self.world_combo.currentData()
    
    def set_missions(self, missions: List[Dict[str, Any]]):
        """
        Set the list of missions.
        
        Args:
            missions: List of mission dicts
        """
        self.missions = missions
        self._update_mission_list()
        
        # Select the first mission if available
        if missions and self.mission_list.count() > 0:
            self.mission_list.setCurrentRow(0)
    
    def _update_mission_list(self):
        """Update the mission list widget with current missions."""
        self.mission_list.clear()
        
        for mission in self.missions:
            item = QListWidgetItem(mission["title"])
            item.setData(Qt.ItemDataRole.UserRole, mission)
            self.mission_list.addItem(item)
    
    def _on_mission_selected(self, current, previous):
        """
        Handle mission selection change.
        
        Args:
            current: Current selected item
            previous: Previously selected item
        """
        if not current:
            self.current_mission = None
            self._clear_mission_details()
            return
        
        # Get the mission data
        self.current_mission = current.data(Qt.ItemDataRole.UserRole)
        self._display_mission(self.current_mission)
    
    def _display_mission(self, mission: Dict[str, Any]):
        """
        Display mission details in the UI.
        
        Args:
            mission: Mission dict to display
        """
        # Set title
        self.title_edit.setText(mission["title"])
        
        # Set description
        self.description_edit.setText(mission["description"])
        
        # Set map description
        self.map_description_edit.setText(mission["map_description"])
        
        # Set structure text
        structure_text = self._format_mission_structure(mission["structure"])
        self.structure_text.setText(structure_text)
    
    def _format_mission_structure(self, structure: Dict[str, Any]) -> str:
        """
        Format the mission structure as readable text.
        
        Args:
            structure: Mission structure dict
            
        Returns:
            Formatted text representation
        """
        text = f"Scenario Type: {structure['scenario_type']['name']}\n\n"
        text += "Details:\n"
        
        for table_name, detail in structure["details"].items():
            text += f"- {table_name}: {detail['name']}\n"
        
        text += "\nReference Chain:\n"
        for ref in structure["references"]:
            text += f"- {ref['phase']}, Table {ref['table_id']}: {ref['result']}\n"
        
        return text
    
    def _clear_mission_details(self):
        """Clear all mission detail fields."""
        self.title_edit.clear()
        self.description_edit.clear()
        self.map_description_edit.clear()
        self.structure_text.clear()
    
    def _on_generate_clicked(self):
        """Handle generate button click."""
        world = self.get_selected_world()
        if not world:
            QMessageBox.warning(self, "Warning", "Please select a world first.")
            return
        
        count = self.count_spin.value()
        use_gpt = self.use_gpt_check.isChecked()
        
        # Emit signal to request mission generation
        self.mission_generated.emit({
            "world": world,
            "count": count,
            "use_gpt": use_gpt
        })
    
    def _on_save_clicked(self):
        """Handle save button click."""
        if not self.current_mission:
            return
        
        # Update mission with edited values
        self.current_mission["title"] = self.title_edit.text()
        self.current_mission["description"] = self.description_edit.toPlainText()
        self.current_mission["map_description"] = self.map_description_edit.toPlainText()
        
        # Update the list item text
        current_item = self.mission_list.currentItem()
        if current_item:
            current_item.setText(self.current_mission["title"])
        
        # Emit signal to save mission
        self.mission_saved.emit(self.current_mission)
        
        QMessageBox.information(self, "Success", "Mission saved successfully.")
    
    def _on_export_clicked(self):
        """Handle export map button click."""
        if not self.current_mission:
            return
        
        # In a real implementation, this would export the map to a VTT format
        # For now, just show a message
        QMessageBox.information(
            self, 
            "Export Map", 
            "Map export functionality will be implemented in a future version."
        )
