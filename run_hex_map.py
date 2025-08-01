import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from view.hex_map_widget import HexMapWidget

def main():
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Hex Map Widget Integration Test")
    main_window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Create hex map widget
    hex_map = HexMapWidget()
    
    # Add some sample systems
    sample_systems = [
        {
            "name": "Test System 1",
            "hex": "0101",
            "x": 1,
            "y": 1,
            "uwp": "A432998-11",
            "bases": "N",
            "zone": "G",
            "pbg": "543",
            "allegiance": "Im",
            "stellar": "M2 V"
        },
        {
            "name": "Test System 2",
            "hex": "0302",
            "x": 3,
            "y": 2,
            "uwp": "B56789A-B",
            "bases": "S",
            "zone": "A",
            "pbg": "654",
            "allegiance": "Zh",
            "stellar": "K1 V"
        },
        {
            "name": "Test System 3",
            "hex": "0504",
            "x": 5,
            "y": 4,
            "uwp": "C6789AB-C",
            "bases": "D",
            "zone": "R",
            "pbg": "765",
            "allegiance": "So",
            "stellar": "G2 V"
        }
    ]
    
    # Set systems
    hex_map.set_systems(sample_systems)
    
    # Add hex map to layout
    layout.addWidget(hex_map)
    
    # Set central widget
    main_window.setCentralWidget(central_widget)
    
    # Show window
    main_window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
