"""Theme Model for TASJ Application.

This module provides the data model for managing application themes. It handles:
- Theme file loading and parsing
- Theme style extraction
- Font mapping for themes

Theme files are stored in config/themes/ with a .theme extension and use INI format:

Example theme file (light.theme):
```ini
[Styles]
QMainWindow { background-color: #ffffff; }
QLabel { color: #000000; }
```

The model maintains theme data without any UI dependencies, following clean
architecture principles.

Classes:
    ThemeModel: Core class for theme data management
"""

import os
import logging
import configparser
from typing import Dict, Any, Optional
from pathlib import Path
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

# Determine the project root directory based on this file's location
# Assumes theme_model.py is in /home/peter/Projects/TASJ/model/
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent # Moves up from /model to /TASJ
_default_themes_dir = _project_root / "config" / "themes"

if not _default_themes_dir.exists():
    logger.warning(f"Calculated themes directory does not exist: {_default_themes_dir}")

class ThemeModel:
    """Model for managing application themes.
    
    This class handles the data layer for theme management, including:
    - Theme file discovery and loading
    - Theme configuration parsing
    - Theme-font mapping
    
    The model operates independently of any UI components, making it suitable
    for testing and reuse.
    
    Attributes:
        themes_dir (Path): Directory containing theme files
        current_theme (str): Name of the currently active theme
        current_stylesheet (str): Stylesheet content of the current theme
    """
    
    def __init__(self, themes_dir: Optional[Path] = None) -> None:
        """Initialize the theme model.
        
        Sets up the themes directory using an absolute path if not provided.
        
        Args:
            themes_dir: Optional path to the themes directory.
        """
        self.themes_dir = themes_dir if themes_dir else _default_themes_dir
        logger.info(f"ThemeModel initialized. Using themes directory: {self.themes_dir.resolve()}")
            
        self.current_theme = "light"  # Default theme
        self.current_stylesheet: str = "" # Default empty stylesheet
        
    def get_available_themes(self) -> list[str]:
        """Get list of available themes using os.listdir.
        
        Scans the themes directory for .theme files and returns their names
        without the extension.
        
        Returns:
            list[str]: Sorted list of available theme names
        """
        themes = []
        logger.info(f"Scanning for themes in (using os.listdir): {self.themes_dir}")
        try:
            if not self.themes_dir.exists() or not self.themes_dir.is_dir():
                logger.error(f"Themes directory not found or not a directory: {self.themes_dir}")
                return []
                
            for item_name in os.listdir(self.themes_dir):
                logger.debug(f"Found item: {item_name}")
                item_path = self.themes_dir / item_name
                if item_path.is_file() and item_name.endswith(".theme"):
                    theme_name = item_name[:-len(".theme")] # Remove .theme extension
                    logger.info(f"Found theme file: {item_name} -> Theme name: {theme_name}")
                    themes.append(theme_name)
        except Exception as e:
            logger.error(f"Error scanning themes directory {self.themes_dir}: {e}", exc_info=True)
            return [] # Return empty list on error
            
        logger.info(f"Available themes found: {themes}")
        return sorted(themes)
        
    def load_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Load theme configuration.
        
        Reads and parses a theme file, extracting styles and other configuration.
        
        Args:
            theme_name (str): Name of the theme to load (case-sensitive, matching filename stem)
            
        Returns:
            Optional[Dict[str, Any]]: Theme data dictionary containing:
                - stylesheet (str): Combined CSS-style rules
                - Other theme-specific settings
                
        Example theme data:
        {
            'stylesheet': 'QMainWindow { background: white; }\nQLabel { color: black; }',
            'accent_color': '#FF0000'
        }
        """
        theme_file = self.themes_dir / f"{theme_name}.theme"
        if not theme_file.exists():
            logger.error(f"Theme file not found: {theme_file}")
            return None
            
        config = configparser.ConfigParser()
        try:
            config.read(theme_file)
            logger.info(f"Successfully loaded theme: {theme_name}")
        except configparser.Error as e:
            logger.error(f"Failed to parse theme file {theme_file}: {e}")
            return None
        
        theme_data = {}
        if 'Styles' in config:
            stylesheet_parts = []
            for selector, style in config['Styles'].items():
                # Correct CSS format: selector { style_properties }
                stylesheet_parts.append(f"{selector} {{ {style} }}")
            theme_data['stylesheet'] = "\n".join(stylesheet_parts)
            logger.debug(f"Generated stylesheet for {theme_name}:\n{theme_data['stylesheet']}")
        else:
            logger.warning(f"No [Styles] section found in theme: {theme_name}")
        
        return theme_data
        
    def load_stylesheet(self, theme_name: str) -> str:
        """Load the stylesheet content for a given theme name.
        
        Args:
            theme_name: The name of the theme (without extension).
            
        Returns:
            The stylesheet content as a string, or an empty string if not found/error.
        """
        if not theme_name:
            logger.warning("Attempted to load stylesheet with empty theme name.")
            return ""
            
        theme_file = self.themes_dir / f"{theme_name}.theme"
        logger.info(f"Attempting to load stylesheet from: {theme_file}")
        
        if not theme_file.exists() or not theme_file.is_file():
            logger.error(f"Theme file not found or not a file: {theme_file}")
            return ""
            
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                self.current_theme = theme_name
                self.current_stylesheet = stylesheet
                logger.info(f"Successfully loaded stylesheet for theme: {theme_name}")
                return stylesheet
        except Exception as e:
            logger.error(f"Error reading theme file {theme_file}: {e}", exc_info=True)
            return ""

    def get_current_theme_name(self) -> Optional[str]:
        return self.current_theme

    def get_theme_font_id(self, theme_name: str) -> str:
        """Get the font ID associated with a theme.
        
        Maps theme names to their corresponding font IDs. Tries to read
        the font_id from the [Font] section of the theme file. Falls back
        to using the theme name as the font ID if not specified.
        
        Args:
            theme_name (str): Name of the theme (case-sensitive, matching filename stem)
            
        Returns:
            str: Font ID for the theme
        """
        theme_file = self.themes_dir / f"{theme_name}.theme"
        if theme_file.exists():
            config = configparser.ConfigParser()
            try:
                config.read(theme_file)
                if 'Font' in config and 'font_id' in config['Font']:
                    font_id = config['Font']['font_id']
                    logger.info(f"Found font_id '{font_id}' in theme {theme_name}")
                    return font_id
                else:
                    logger.warning(f"No [Font] section or font_id found in {theme_name}, falling back to theme name.")
            except configparser.Error as e:
                logger.error(f"Failed to parse theme file {theme_file} for font_id: {e}")
        else:
            logger.warning(f"Theme file {theme_file} not found for font_id lookup.")
            
        # Fallback to using theme name as font ID
        logger.info(f"Using theme name '{theme_name}' as font_id fallback.")
        return theme_name
