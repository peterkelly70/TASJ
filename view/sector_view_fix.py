"""
This is a temporary file containing the corrected methods for SectorView.
"""

def _on_milieu_changed(self, milieu):
    """Handle milieu selection change."""
    if milieu != self.current_milieu:
        # Update current milieu
        self.current_milieu = milieu
        
        # Save preference
        self.settings.save_milieu(milieu)
        
        # Emit signal for other components
        self.milieu_changed.emit(milieu)
        
        # Reload sectors list with the new milieu
        self._reload_sectors_for_milieu(milieu)
        
        # Update current sector if one is selected
        if self.current_sector:
            self.map_tabs.set_sector(self.current_sector, milieu)
            self._load_systems_for_sector(self.current_sector)

def _reload_sectors_for_milieu(self, milieu):
    """Reload sectors list for the selected milieu."""
    try:
        # Get sectors from the database filtered by milieu
        from controller.sectors_controller import SectorController
        sectors_controller = SectorController(db_path=self.db_path)
        sectors = sectors_controller.get_sectors_by_milieu(milieu)
        
        # Convert DB records to dictionaries
        sector_dicts = []
        for sector in sectors:
            sector_id, name, x, y, desc, img_path, abbrev, milieu = sector
            sector_dicts.append({
                "sector_id": sector_id,
                "name": name or f"Unnamed Sector {sector_id}",
                "x_coordinate": x,
                "y_coordinate": y,
                "description": desc,
                "image_path": img_path,
                "abbreviation": abbrev,
                "milieu": milieu
            })
        
        # Update sectors list
        self.set_sectors(sector_dicts)
        
        # Clear current sector if it's not in the new milieu
        if self.current_sector:
            found = False
            for sector in sector_dicts:
                if sector["sector_id"] == self.current_sector.get("sector_id"):
                    found = True
                    break
            if not found:
                self.current_sector = None
                self.sector_header.setText("Select a Sector")
                self.systems_list.clear()
    except Exception as e:
        logger.error(f"Error loading sectors for milieu {milieu}: {e}")
        self.sectors_list.clear()
        self.sectors_list.addItem(f"Error: {str(e)}")

def set_db_path(self, db_path):
    """Set the database path."""
    self.db_path = db_path
    self.map_tabs.set_db_path(db_path)
