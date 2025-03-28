import os
import json
import shutil
import zipfile
import logging
import tempfile
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase

logger = logging.getLogger(__name__)

class FontModel:
    """Model for managing font data and operations."""
    
    def __init__(self) -> None:
        self.fonts_dir = Path("config/fonts")
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_data = self._load_fonts_data()
        self.installed_fonts_path = Path("config/installed_fonts.json")
        self.installed_fonts = self._load_installed_fonts()
        # self.save_installed_fonts() # No need to save immediately on load

    def _load_fonts_data(self) -> Dict[str, Any]:
        """Load font configuration data."""
        try:
            with open("config/licenses/fonts.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fonts data: {e}", exc_info=True)
            return {"fonts": {}}
    
    def get_font_info(self, font_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific font."""
        return self.fonts_data["fonts"].get(font_id)
    
    def is_font_installed(self, font_id: str) -> bool:
        """Check if a font is installed in the application's font directory."""
        font_info = self.get_font_info(font_id)
        if not font_info:
            return False
        font_path = self.fonts_dir / font_info["filename"]
        return font_path.exists()
    
    def _download_file(self, url: str) -> bytes:
        """Download a file from a URL."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        content = bytes()
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
        return content
    
    def _extract_font_from_archive(self, archive_data: bytes, font_info: Dict[str, Any]) -> Path:
        """Extract a font file from a ZIP archive."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_file.write(archive_data)
            temp_file.flush()
            
            target_path = self.fonts_dir / font_info["filename"]
            
            with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                zip_ref.extract(font_info["archive_path"], self.fonts_dir)
            
            # Move to final location if needed
            extracted_path = self.fonts_dir / font_info["archive_path"]
            if extracted_path != target_path:
                shutil.move(str(extracted_path), str(target_path))
                # Clean up empty directories
                parent_dir = extracted_path.parent
                while parent_dir != self.fonts_dir:
                    try:
                        parent_dir.rmdir()
                        parent_dir = parent_dir.parent
                    except OSError:
                        break
            
            os.unlink(temp_file.name)
            return target_path
    
    def install_font(self, font_id: str) -> Optional[str]:
        """Download and install a font, return the font path if successful."""
        font_info = self.get_font_info(font_id)
        if not font_info:
            logger.error(f"Unknown font ID: {font_id}")
            return None
            
        font_path = self.fonts_dir / font_info["filename"]
        if font_path.exists():
            return str(font_path)
            
        try:
            # Download the font file
            content = self._download_file(font_info["download_url"])
            
            # Handle zip archives
            if font_info.get("archive", False):
                font_path = self._extract_font_from_archive(content, font_info)
            else:
                # Direct download of TTF file
                with open(font_path, 'wb') as f:
                    f.write(content)
                    
            # Register font with Qt
            font_db_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_db_id == -1:
                logger.error(f"Failed to register font: {font_info['filename']}")
                return None
                
            loaded_families = QFontDatabase.applicationFontFamilies(font_db_id)
            if loaded_families:
                font_info["family_name"] = loaded_families[0]
                logger.info(f"Successfully loaded font: {font_info['name']} ({font_info['family_name']}) from {font_path}")
                # Store details for this specific file if needed, potentially under the main font_id
                # Mark the main font_id as successfully installed if at least one file loads
                at_least_one_loaded = True
            else:
                logger.warning(f"Loaded font {font_path} but couldn't get family name.")
                # Remove if family name is crucial?
                # QFontDatabase.removeApplicationFont(font_db_id) 

            if not at_least_one_loaded:
                 logger.error(f"Failed to load any font files for font ID: {font_id}")
                 # Clean up potentially extracted files if the whole process failed?
                 return None

            logger.info(f"Successfully installed and loaded font: {font_info['name']}")
            # Ensure install_path is stored, needed for get_installed_app_font_families fallback
            font_info['install_path'] = str(font_path) 
            self.installed_fonts[font_id] = font_info
            self.save_installed_fonts()
            return str(font_path) # Return install directory path

        except Exception as e:
            logger.error(f"Failed to download font {font_info['name']}: {e}", exc_info=True)
            return None
    
    def ensure_font_loaded(self, font_id: str) -> Optional[str]:
        """Ensure a font is loaded, return the font path if successful."""
        font_info = self.get_font_info(font_id)
        if not font_info:
            logger.error(f"Unknown font ID: {font_id}")
            return None
            
        font_path = self.fonts_dir / font_info["filename"]
        if font_path.exists():
            return str(font_path)
            
        try:
            # Register font with Qt
            font_db_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_db_id == -1:
                logger.error(f"Failed to register font: {font_info['filename']}")
                return None
                
            loaded_families = QFontDatabase.applicationFontFamilies(font_db_id)
            if loaded_families:
                font_info["family_name"] = loaded_families[0]
                logger.info(f"Successfully loaded font: {font_info['name']} ({font_info['family_name']}) from {font_path}")
                # Store details for this specific file if needed, potentially under the main font_id
                # Mark the main font_id as successfully installed if at least one file loads
                at_least_one_loaded = True
            else:
                logger.warning(f"Loaded font {font_path} but couldn't get family name.")
                # Remove if family name is crucial?
                # QFontDatabase.removeApplicationFont(font_db_id) 

            if not at_least_one_loaded:
                 logger.error(f"Failed to load any font files for font ID: {font_id}")
                 # Clean up potentially extracted files if the whole process failed?
                 return None

            logger.info(f"Successfully installed and loaded font: {font_info['name']}")
            # Ensure install_path is stored, needed for get_installed_app_font_families fallback
            font_info['install_path'] = str(font_path) 
            self.installed_fonts[font_id] = font_info
            self.save_installed_fonts()
            return str(font_path) # Return install directory path

        except Exception as e:
            logger.error(f"Failed to load font {font_info['name']}: {e}", exc_info=True)
            return None
    
    def create_font(self, font_id: str, size: int = 10) -> Optional[QFont]:
        """Create a QFont object for the specified font ID."""
        if not self.is_font_installed(font_id):
            return None
            
        font_info = self.get_font_info(font_id)
        if not font_info:
            return None
            
        return QFont(font_info["filename"].replace(".ttf", ""), size)

    def _load_installed_fonts(self) -> Dict[str, Any]:
        """Load the record of installed fonts from JSON."""
        if self.installed_fonts_path.exists():
            try:
                with open(self.installed_fonts_path, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} installed font records from {self.installed_fonts_path}")
                    return data
            except Exception as e:
                logger.error(f"Failed to load installed fonts file: {e}", exc_info=True)
                # If loading fails, maybe start fresh or attempt recovery?
        return {}

    def get_installed_app_font_families(self) -> List[str]:
        """Get a list of font families installed by the application."""
        families = set()
        for font_id, details in self.installed_fonts.items():
            family_name = details.get('family_name')
            if family_name:
                families.add(family_name)
            else:
                 # Fallback: If family_name wasn't stored (e.g., older install), try getting it now
                 # This should be less common with the improved install_font
                 try:
                     install_path_str = details.get('install_path')
                     files = details.get('files')
                     if install_path_str and files:
                         font_path = Path(install_path_str) / files[0] # Assuming first file
                         if font_path.exists():
                             temp_font_id = QFontDatabase.addApplicationFont(str(font_path))
                             if temp_font_id != -1:
                                 loaded_families = QFontDatabase.applicationFontFamilies(temp_font_id)
                                 if loaded_families:
                                     family_name = loaded_families[0]
                                     families.add(family_name)
                                     # Optionally update self.installed_fonts[font_id]['family_name'] and save?
                                     logger.info(f"Determined family name for {font_id} on the fly: {family_name}")
                                 QFontDatabase.removeApplicationFont(temp_font_id) # Clean up
                 except Exception as e:
                     logger.warning(f"Fallback check failed for font_id {font_id}: {e}")
                 
                 # If still no family name after fallback, use font_id
                 if not family_name:
                     logger.warning(f"Using font_id '{font_id}' as fallback family name after check.")
                     families.add(font_id)
                     
        return sorted(list(families))

    def get_font_config(self, font_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration details for a specific font ID."""
        return self.installed_fonts.get(font_id)
        
    def get_available_uninstalled_fonts(self) -> Dict[str, Dict[str, Any]]:
        """Get fonts defined in fonts.json but not listed as installed."""
        uninstalled = {}
        all_available = self.fonts_data["fonts"] # Reuse existing method
        for font_id, config in all_available.items():
            if font_id not in self.installed_fonts:
                # Basic check: is it in the installed_fonts dictionary?
                uninstalled[font_id] = config
            else:
                # Deeper check: Verify font files actually exist where expected
                # This handles cases where the record exists but install failed/was deleted
                if not self._check_font_files_exist(font_id):
                    logger.warning(f"Font '{font_id}' in installed record, but files missing. Marking as uninstalled.")
                    uninstalled[font_id] = config
                    # Optionally remove the bad record from self.installed_fonts here?
                    # del self.installed_fonts[font_id]
                    # self.save_installed_fonts()
                    
        logger.info(f"Found {len(uninstalled)} available but uninstalled fonts.")
        return uninstalled

    def _check_font_files_exist(self, font_id: str) -> bool:
        """Check if all files for a given installed font_id exist on disk."""
        if font_id not in self.installed_fonts:
            return False # Not considered installed
            
        details = self.installed_fonts[font_id]
        install_path_str = details.get('install_path')
        files = details.get('files')
        
        if not install_path_str or not files:
            logger.warning(f"Missing install_path or files data for installed font '{font_id}'. Assuming files missing.")
            return False # Missing data means we can't verify
            
        font_path_base = Path(install_path_str)
        for filename in files:
            if not (font_path_base / filename).exists():
                logger.debug(f"File missing for font '{font_id}': {font_path_base / filename}")
                return False # Found a missing file
                
        return True # All expected files exist

    def save_installed_fonts(self):
        try:
            with open(self.installed_fonts_path, "w") as f:
                json.dump(self.installed_fonts, f, indent=2) # Add indent for readability
            logger.info(f"Saved {len(self.installed_fonts)} installed font records to {self.installed_fonts_path}")
        except Exception as e:
            logger.error(f"Failed to save installed fonts: {e}", exc_info=True)
