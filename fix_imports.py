#!/usr/bin/env python3
"""
Script to fix circular imports in the TASJ application.
This will modify the necessary files to break circular dependencies.
"""

import os
import re

def fix_map_tabs_widget():
    """Fix the map_tabs_widget.py file to avoid circular imports."""
    filepath = "view/map_tabs_widget.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Remove the import of MapTabsWidget from sector_view
    content = content.replace(
        "from view.sector_view import SectorMapWidget", 
        "# SectorMapWidget will be imported when needed"
    )
    
    # Add proper lazy imports
    if "def set_sector" in content:
        content = re.sub(
            r'def set_sector\(self, sector, milieu=None\):(.*?)# Create map widgets',
            'def set_sector(self, sector, milieu=None):\\1# Import here to avoid circular imports\\n        from view.sector_view import SectorMapWidget\\n\\n        # Create map widgets',
            content, 
            flags=re.DOTALL
        )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print(f"Fixed {filepath}")

def fix_sector_view():
    """Fix the sector_view.py file to avoid circular imports."""
    filepath = "view/sector_view.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Remove the import of MapTabsWidget
    content = content.replace(
        "from view.map_tabs_widget import MapTabsWidget", 
        "# MapTabsWidget will be imported when needed"
    )
    
    # Add proper lazy imports in _setup_ui method
    if "def _setup_ui" in content and "self.map_tabs = MapTabsWidget" in content:
        content = re.sub(
            r'# Map tabs widget\s+self\.map_tabs = MapTabsWidget',
            '# Map tabs widget\\n        from view.map_tabs_widget import MapTabsWidget\\n        self.map_tabs = MapTabsWidget',
            content
        )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    # Change to the project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Fix the files
    fix_map_tabs_widget()
    fix_sector_view()
    
    print("Import fixes completed. Try running the application now.")
