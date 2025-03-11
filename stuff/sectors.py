from PyQt5.QtWidgets import QListWidgetItem, QLabel, QPushButton, QTextEdit, QVBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from database import TravellerDatabase

class Sector:
    def __init__(self, db: TravellerDatabase):
        self.db = db

    def get_all_sectors(self):
        return self.db.read_records('sectors', {})

    def create_sector(self, sector_data):
        self.db.create_record('sectors', sector_data)

    def get_sector(self, sector_id):
        sectors = self.db.read_records('sectors', {'sector_id': sector_id})
        return sectors[0] if sectors else None

    def update_sector(self, sector_id, sector_data):
        self.db.update_record('sectors', sector_data, {'sector_id': sector_id})

    def delete_sector(self, sector_id):
        self.db.delete_record('sectors', {'sector_id': sector_id})

    def display_sector_info(self, sector_id, sector_info_text, sector_map_label):
        sector = self.get_sector(sector_id)
        if sector:
            sector_info_text.setText(f"Name: {sector['name']}\nDescription: {sector['description']}")
            if sector['image_path']:
                pixmap = QPixmap(sector['image_path'])
                sector_map_label.setPixmap(pixmap.scaled(sector_map_label.size(), Qt.KeepAspectRatio))
            else:
                sector_map_label.setText("No Map Available")

    def add_sector(self, sector_list, sector_info_text, sector_map_label):
        # This would open a dialog to input new sector data
        # For simplicity, let's assume sector_data is collected
        sector_data = {
            "name": "New Sector",
            "description": "Description of the sector",
            "x_coordinate": 100,
            "y_coordinate": 200,
            "image_path": ""  # Would be set by a file dialog
        }
        self.create_sector(sector_data)
        item = QListWidgetItem(sector_data['name'])
        item.setData(Qt.UserRole, sector_data['sector_id'])
        sector_list.addItem(item)
        sector_info_text.clear()
        sector_map_label.clear()

    def edit_sector(self, sector_id, sector_info_text, sector_map_label):
        # Similar to add_sector but fetches existing data and updates
        sector = self.get_sector(sector_id)
        if sector:
            sector_data = {
                "name": sector["name"],
                "description": sector["description"],
                "x_coordinate": sector["x_coordinate"],
                "y_coordinate": sector["y_coordinate"],
                "image_path": sector["image_path"]
            }
            self.update_sector(sector_id, sector_data)
            sector_info_text.setText(f"Name: {sector_data['name']}\nDescription: {sector_data['description']}")
            if sector_data["image_path"]:
                pixmap = QPixmap(sector_data["image_path"])
                sector_map_label.setPixmap(pixmap.scaled(sector_map_label.size(), Qt.KeepAspectRatio))

    def delete_sector(self, sector_id, sector_list, sector_info_text, sector_map_label):
        self.delete_sector(sector_id)
        sector_list.clear()
        sector_info_text.clear()
        sector_map_label.clear()

    def load_sectors(self, sector_list):
        sectors = self.get_all_sectors()
        for sector in sectors:
            item = QListWidgetItem(sector['name'])
            item.setData(Qt.UserRole, sector['sector_id'])
            sector_list.addItem(item)
