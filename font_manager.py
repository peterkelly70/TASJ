import os
import json
import shutil
import zipfile
import logging
import tempfile
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtGui import QFont, QFontDatabase

logger = logging.getLogger(__name__)

class FontManager:
    """Manages font downloads and installation."""
    
    def __init__(self) -> None:
        self.fonts_dir = Path("config/fonts")
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_data = self._load_fonts_data()
        
    def _load_fonts_data(self) -> Dict[str, Any]:
        """Load font configuration data."""
        try:
            with open("config/licenses/fonts.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fonts data: {e}", exc_info=True)
            return {"fonts": {}}
            
    def is_font_installed(self, font_id: str) -> bool:
        """Check if a font is installed in the application's font directory."""
        if font_id not in self.fonts_data["fonts"]:
            return False
            
        font_info = self.fonts_data["fonts"][font_id]
        font_path = self.fonts_dir / font_info["filename"]
        return font_path.exists()
        
    def download_font(self, font_id: str, parent: Optional[QWidget] = None) -> bool:
        """Download and install a font if not already present."""
        if font_id not in self.fonts_data["fonts"]:
            logger.error(f"Unknown font ID: {font_id}")
            return False
            
        font_info = self.fonts_data["fonts"][font_id]
        font_path = self.fonts_dir / font_info["filename"]
        
        if font_path.exists():
            return True
            
        # Ask for permission
        if parent and not self._confirm_download(font_info, parent):
            return False
            
        try:
            # Download the font file
            response = requests.get(font_info["download_url"], stream=True)
            response.raise_for_status()
            
            # Handle zip archives
            if font_info.get("archive", False):
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                    # Download to temp file
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_file.flush()
                    
                    # Extract the specific font file
                    with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                        zip_ref.extract(font_info["archive_path"], self.fonts_dir)
                    
                    # Move to final location if needed
                    extracted_path = self.fonts_dir / font_info["archive_path"]
                    if extracted_path != font_path:
                        shutil.move(str(extracted_path), str(font_path))
                        # Clean up empty directories
                        parent_dir = extracted_path.parent
                        while parent_dir != self.fonts_dir:
                            try:
                                parent_dir.rmdir()
                                parent_dir = parent_dir.parent
                            except OSError:
                                break
                                
                os.unlink(temp_file.name)
            else:
                # Direct download of TTF file
                with open(font_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            # Register font with Qt
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id == -1:
                logger.error(f"Failed to register font: {font_info['filename']}")
                return False
                
            logger.info(f"Successfully installed font: {font_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download font {font_info['name']}: {e}", exc_info=True)
            if parent:
                QMessageBox.critical(parent, "Error",
                    f"Failed to download font {font_info['name']}: {str(e)}")
            return False
            
    def _confirm_download(self, font_info: Dict[str, Any], parent: QWidget) -> bool:
        """Ask for user permission to download a font."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Download Font")
        msg.setText(f"The font '{font_info['name']}' is not installed.")
        msg.setInformativeText(
            f"This font is needed for the {font_info['usage']}.\n\n"
            f"Would you like to download it from:\n{font_info['source']}?\n\n"
            f"License: {font_info['license']}"
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        return msg.exec() == QMessageBox.StandardButton.Yes
        
    def get_font(self, font_id: str, size: int = 10) -> Optional[QFont]:
        """Get a QFont object for the specified font ID."""
        if not self.is_font_installed(font_id):
            return None
            
        font_info = self.fonts_data["fonts"][font_id]
        return QFont(font_info["filename"].replace(".ttf", ""), size)
