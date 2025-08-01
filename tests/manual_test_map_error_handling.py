#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manual test script for map error handling.

This script creates a simple application that demonstrates the error handling
in the map widgets without relying on the full widget hierarchy, avoiding
circular import issues.
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QPushButton, QLabel, QTabWidget, QStatusBar
)
from PyQt6.QtCore import Qt

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ErrorTestWindow(QMainWindow):
    """Test window for map error handling."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Error Handling Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create test buttons
        self.create_test_buttons(layout)
        
        # Import widgets here to avoid circular imports in the test
        try:
            from view.sector_view import SectorMapWidget
            from view.map_tabs_widget import SystemMapWidget
            from view.planet_map_widget import PlanetMapWidget
            
            # Create widgets
            self.sector_map = SectorMapWidget()
            self.system_map = SystemMapWidget()
            self.planet_map = PlanetMapWidget()
            
            # Connect error signals
            self.sector_map.map_error.connect(self.on_map_error)
            self.system_map.map_error.connect(self.on_map_error)
            self.planet_map.map_error.connect(self.on_map_error)
            
            # Add widgets to tabs
            self.tab_widget.addTab(self.sector_map, "Sector Map")
            self.tab_widget.addTab(self.system_map, "System Map")
            self.tab_widget.addTab(self.planet_map, "Planet Map")
            
            self.widgets_loaded = True
            logger.info("All map widgets loaded successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import map widgets: {e}")
            error_label = QLabel(f"Failed to load map widgets: {e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            self.widgets_loaded = False
    
    def create_test_buttons(self, layout):
        """Create buttons for testing error handling."""
        button_layout = QVBoxLayout()
        
        # Create test buttons
        self.test_sector_button = QPushButton("Test Sector Map Error")
        self.test_sector_button.clicked.connect(self.test_sector_map_error)
        button_layout.addWidget(self.test_sector_button)
        
        self.test_system_button = QPushButton("Test System Map Error")
        self.test_system_button.clicked.connect(self.test_system_map_error)
        button_layout.addWidget(self.test_system_button)
        
        self.test_planet_button = QPushButton("Test Planet Map Error")
        self.test_planet_button.clicked.connect(self.test_planet_map_error)
        button_layout.addWidget(self.test_planet_button)
        
        layout.addLayout(button_layout)
    
    def on_map_error(self, error_message):
        """Handle map error messages."""
        logger.info(f"Map error received: {error_message}")
        self.status_bar.showMessage(f"Error: {error_message}", 5000)
    
    def test_sector_map_error(self):
        """Test sector map error handling."""
        if not hasattr(self, 'widgets_loaded') or not self.widgets_loaded:
            self.status_bar.showMessage("Widgets not loaded, cannot test", 5000)
            return
            
        logger.info("Testing sector map error handling")
        self.tab_widget.setCurrentIndex(0)  # Switch to sector map tab
        
        # Force an error by setting an invalid sector name
        from unittest.mock import MagicMock
        self.sector_map.api = MagicMock()
        self.sector_map.api.get_sector_map.return_value = (None, "Test sector map error")
        
        # Load a sector map with the mocked API
        self.sector_map.sector_name = "InvalidSector"
        self.sector_map.loading_error = False
        self.sector_map.error_message = ""
        
        # Simulate loading
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class MockThread(QThread):
            load_failed = pyqtSignal(str)
            
            def run(self):
                self.load_failed.emit("Test sector map error")
        
        thread = MockThread()
        thread.load_failed.connect(self.sector_map._on_load_failed)
        thread.start()
    
    def test_system_map_error(self):
        """Test system map error handling."""
        if not hasattr(self, 'widgets_loaded') or not self.widgets_loaded:
            self.status_bar.showMessage("Widgets not loaded, cannot test", 5000)
            return
            
        logger.info("Testing system map error handling")
        self.tab_widget.setCurrentIndex(1)  # Switch to system map tab
        
        # Force an error by setting an invalid system
        from unittest.mock import MagicMock
        self.system_map.api = MagicMock()
        self.system_map.api.get_system_map.return_value = (None, "Test system map error")
        
        # Set system data
        system_data = {"name": "TestSystem", "sector": "TestSector", "hex": "0101"}
        self.system_map.set_system(system_data, [])
    
    def test_planet_map_error(self):
        """Test planet map error handling."""
        if not hasattr(self, 'widgets_loaded') or not self.widgets_loaded:
            self.status_bar.showMessage("Widgets not loaded, cannot test", 5000)
            return
            
        logger.info("Testing planet map error handling")
        self.tab_widget.setCurrentIndex(2)  # Switch to planet map tab
        
        # Force an error in the planet map
        self.planet_map.get_map_from_db = MagicMock(return_value=None)
        
        # Mock the download thread to emit an error
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class MockThread(QThread):
            download_failed = pyqtSignal(str)
            
            def run(self):
                self.download_failed.emit("Test planet map download error")
        
        # Set planet data to trigger map loading
        planet_data = {"name": "TestPlanet", "uwp": "X123456-7"}
        self.planet_map.set_planet(planet_data)
        
        # Replace the download thread with our mock
        if hasattr(self.planet_map, 'downloader_thread') and self.planet_map.downloader_thread:
            self.planet_map.downloader_thread.quit()
            self.planet_map.downloader_thread.wait()
        
        thread = MockThread()
        thread.download_failed.connect(self.planet_map._on_download_failed)
        thread.start()

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    window = ErrorTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
