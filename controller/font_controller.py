import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QListWidgetItem
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from model.font_model import FontModel
from view.font_dialog import FontDownloadDialog, FontLicenseDialog

logger = logging.getLogger(__name__)

class FontController:
    """Controller for managing fonts and related UI interactions."""
    
    def __init__(self) -> None:
        self.model = FontModel()
        
    def ensure_font_available(self, font_id: str, parent: Optional[QWidget] = None) -> Optional[QFont]:
        """Ensure a font is available, downloading if necessary and approved."""
        # Check if already installed
        if self.model.is_font_installed(font_id):
            return self.model.create_font(font_id)
            
        # Get font info
        font_info = self.model.get_font_info(font_id)
        if not font_info:
            logger.error(f"Unknown font ID: {font_id}")
            return None
            
        # Ask for permission to download
        if parent:
            dialog = FontDownloadDialog(font_info, parent)
            if dialog.exec() != FontDownloadDialog.DialogCode.Accepted:
                logger.info(f"User declined to download font: {font_info['name']}")
                return None
                
        # Install the font
        font_path = self.model.install_font(font_id)
        if not font_path:
            return None
            
        return self.model.create_font(font_id)
    
    def get_installed_app_font_families(self) -> List[str]:
        """Get a list of font families installed by the application."""
        return self.model.get_installed_app_font_families()

    def get_available_uninstalled_fonts(self) -> Dict[str, Dict[str, Any]]:
        """Get fonts defined in fonts.json but not listed as installed."""
        return self.model.get_available_uninstalled_fonts()

    def show_licenses(self, parent: Optional[QWidget] = None) -> None:
        """Show the font licenses dialog."""
        dialog = FontLicenseDialog(parent)
        
        # Populate font list
        for font_id, font_info in self.model.fonts_data["fonts"].items():
            item = QListWidgetItem(font_info["name"])
            item.setData(Qt.ItemDataRole.UserRole, font_id)
            dialog.font_list.addItem(item)
            
        # Connect selection change
        def update_font_details(current: QListWidgetItem, previous: Optional[QListWidgetItem] = None) -> None:
            if not current:
                return
                
            font_id = current.data(Qt.ItemDataRole.UserRole)
            font_info = self.model.get_font_info(font_id)
            if not font_info:
                return
                
            dialog.name_label.setText(font_info["name"])
            dialog.author_label.setText(font_info["author"])
            dialog.description_label.setText(font_info["description"])
            dialog.usage_label.setText(font_info["usage"])
            dialog.source_label.setText(
                f"<a href='{font_info['source']}'>{font_info['source']}</a>"
            )
            
            # Load license text
            if font_info["license_file"]:
                try:
                    license_path = Path("config/licenses") / font_info["license_file"]
                    with open(license_path, "r") as f:
                        dialog.license_text.setText(f.read())
                except Exception as e:
                    dialog.license_text.setText(f"Error loading license text: {str(e)}")
            else:
                dialog.license_text.setText(
                    f"License: {font_info['license']}\n"
                    "No detailed license text available."
                )
                
        dialog.font_list.currentItemChanged.connect(update_font_details)
        if dialog.font_list.count() > 0:
            dialog.font_list.setCurrentRow(0)
            
        dialog.exec()
