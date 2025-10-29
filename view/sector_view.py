from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QListWidget, QSplitter, QGroupBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt

class SectorView(QWidget):
    """Galaxy view implementing the layout from the wireframe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the Galaxy tab UI layout."""
        # Main layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        # Create the main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Sectors and Systems lists with search
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setLayout(left_layout)
        
        # Sector search
        sector_search_layout = QHBoxLayout()
        sector_search_label = QLabel("Sector Search:")
        self.sector_search_input = QLineEdit()
        sector_search_layout.addWidget(sector_search_label)
        sector_search_layout.addWidget(self.sector_search_input)
        left_layout.addLayout(sector_search_layout)
        
        # Sectors list
        sectors_label = QLabel("Sectors")
        sectors_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        left_layout.addWidget(sectors_label)
        
        self.sectors_list = QListWidget()
        self.sectors_list.setMinimumHeight(200)
        left_layout.addWidget(self.sectors_list)
        
        # System search
        system_search_layout = QHBoxLayout()
        system_search_label = QLabel("System Search:")
        self.system_search_input = QLineEdit()
        system_search_layout.addWidget(system_search_label)
        system_search_layout.addWidget(self.system_search_input)
        left_layout.addLayout(system_search_layout)
        
        # Systems list
        systems_label = QLabel("Systems")
        systems_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        left_layout.addWidget(systems_label)
        
        self.systems_list = QListWidget()
        self.systems_list.setMinimumHeight(200)
        left_layout.addWidget(self.systems_list)
        
        # Right panel with map tabs and info panels
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setLayout(right_layout)
        
        # Map tabs
        self.map_tabs = QTabWidget()
        self.galaxy_map_tab = QWidget()
        self.sector_map_tab = QWidget()
        self.planet_map_tab = QWidget()
        
        # Add placeholder content for each map tab
        galaxy_layout = QVBoxLayout(self.galaxy_map_tab)
        self.galaxy_map_label = QLabel("Galaxy map not generated yet")
        self.galaxy_map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.galaxy_map_label.setScaledContents(True)
        galaxy_layout.addWidget(self.galaxy_map_label)
        self.generate_galaxy_button = QPushButton("Generate Galaxy Map")
        galaxy_layout.addWidget(self.generate_galaxy_button)

        sector_layout = QVBoxLayout(self.sector_map_tab)
        self.sector_map_label = QLabel("Sector map not generated yet")
        self.sector_map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sector_map_label.setScaledContents(True)
        sector_layout.addWidget(self.sector_map_label)
        self.generate_sector_button = QPushButton("Generate Sector Map")
        sector_layout.addWidget(self.generate_sector_button)

        planet_layout = QVBoxLayout(self.planet_map_tab)
        self.planet_map_label = QLabel("Select a planet and generate a map")
        self.planet_map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.planet_map_label.setScaledContents(True)
        planet_layout.addWidget(self.planet_map_label)
        self.generate_planet_button = QPushButton("Generate Planet Map")
        self.generate_planet_button.setEnabled(False)
        planet_layout.addWidget(self.generate_planet_button)

        # Add tabs to tab widget
        self.map_tabs.addTab(self.galaxy_map_tab, "Galaxy Map")
        self.map_tabs.addTab(self.sector_map_tab, "Sector Map")
        self.map_tabs.addTab(self.planet_map_tab, "Planet Map")
        
        right_layout.addWidget(self.map_tabs)
        
        # Bottom info panels
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_panel.setLayout(bottom_layout)
        
        # Sector info panel
        self.sector_info_group = QGroupBox("Sector Info")
        sector_info_layout = QVBoxLayout()
        self.sector_info_content = QLabel("Sector information will appear here")
        sector_info_layout.addWidget(self.sector_info_content)
        self.sector_info_group.setLayout(sector_info_layout)
        bottom_layout.addWidget(self.sector_info_group)
        
        # System info panel
        self.system_info_group = QGroupBox("System Info")
        system_info_layout = QVBoxLayout()
        self.system_info_content = QLabel("System information will appear here")
        system_info_layout.addWidget(self.system_info_content)
        self.system_info_group.setLayout(system_info_layout)
        bottom_layout.addWidget(self.system_info_group)
        
        # Planets list panel
        self.planets_group = QGroupBox("List of planets in system - clickable")
        planets_layout = QVBoxLayout()
        self.planets_list = QListWidget()
        planets_layout.addWidget(self.planets_list)
        self.planets_group.setLayout(planets_layout)
        bottom_layout.addWidget(self.planets_group)
        
        # Planet info panel
        self.planet_info_group = QGroupBox("Planet Info")
        planet_info_layout = QVBoxLayout()
        self.planet_info_content = QLabel("Planet information will appear here")
        planet_info_layout.addWidget(self.planet_info_content)
        self.planet_info_group.setLayout(planet_info_layout)
        bottom_layout.addWidget(self.planet_info_group)
        
        right_layout.addWidget(bottom_panel)
        
        # Add panels to the main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Set the stretch factors
        main_splitter.setStretchFactor(0, 1)  # Left panel (30%)
        main_splitter.setStretchFactor(1, 2)  # Right panel (70%)
