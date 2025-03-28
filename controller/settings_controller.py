"""Settings Controller for TASJ Application.

This module provides persistent settings management for the application,
handling:
- Window state and geometry
- Theme preferences
- Font preferences
- Other application settings

The controller uses QSettings for persistent storage, providing a
platform-independent way to store application preferences.

Example usage:
```python
settings = SettingsController()
settings.save_theme("dark")
current_theme = settings.load_theme()
settings.save_window_geometry(window.saveGeometry())
```

Classes:
    SettingsController: Core class for settings management
"""

import logging
from typing import Any, Optional
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class SettingsController:
    """Controller for managing application settings.
    
    This class provides a centralized way to manage application settings,
    including:
    - Persistent storage of settings
    - Type-safe setting retrieval
    - Default value handling
    
    Settings are stored using QSettings with organization 'Codeium' and
    application 'TASJ'.
    
    The controller handles serialization and deserialization of complex
    types like QFont and window geometry.
    """
    
    def __init__(self) -> None:
        """Initialize the settings controller.
        
        Creates a QSettings instance for 'Codeium'/'TASJ' and sets up
        any default values needed.
        """
        self.settings = QSettings('Codeium', 'TASJ')
        
    def get_value(self, key: str, default: Any = None, value_type: Any = None) -> Any:
        """Get a setting value.
        
        Provides type-safe retrieval of settings with default value support.
        
        Args:
            key (str): Setting key to retrieve
            default (Any, optional): Default value if setting doesn't exist
            value_type (Any, optional): Type to convert the value to
            
        Returns:
            Any: The setting value, converted to value_type if specified
            
        Example:
            >>> settings.get_value("max_items", 10, int)
            10
        """
        return self.settings.value(key, default, type=value_type)
        
    def set_value(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Stores a value in the settings database.
        
        Args:
            key (str): Setting key to store
            value (Any): Value to store
            
        The value will be automatically serialized by QSettings based
        on its type.
        """
        self.settings.setValue(key, value)
        
    def save_window_geometry(self, geometry: bytes) -> None:
        """Save window geometry.
        
        Stores the main window's geometry for restoration on next launch.
        
        Args:
            geometry (bytes): Window geometry from QWidget.saveGeometry()
        """
        self.settings.setValue("window_geometry", geometry)
        
    def load_window_geometry(self) -> Optional[bytes]:
        """Load window geometry.
        
        Retrieves saved window geometry for restoring window state.
        
        Returns:
            Optional[bytes]: Saved geometry or None if not available
        """
        return self.settings.value("window_geometry")
        
    def save_theme(self, theme_name: str) -> None:
        """Save current theme.
        
        Stores the user's theme preference.
        
        Args:
            theme_name (str): Name of the selected theme
        """
        self.settings.setValue("theme", theme_name)
        
    def load_theme(self) -> str:
        """Load saved theme.
        
        Retrieves the user's theme preference.
        
        Returns:
            str: Theme name, defaults to "light" if not set
        """
        return self.settings.value("theme", "light")
        
    def save_font(self, font: QFont) -> None:
        """Save custom font.
        
        Stores the user's font preference.
        
        Args:
            font (QFont): The font to save
            
        The font is stored as a string representation that can be
        used to recreate the QFont object.
        """
        self.settings.setValue("custom_font", font.toString())
        
    def load_font(self) -> Optional[QFont]:
        """Load custom font.
        
        Retrieves and reconstructs the user's font preference.
        
        Returns:
            Optional[QFont]: The saved font or None if not available
            
        The method attempts to reconstruct the QFont from its string
        representation. Returns None if the font string is invalid
        or not available.
        """
        font_str = self.settings.value("custom_font")
        if font_str:
            font = QFont()
            if font.fromString(font_str):
                return font
        return None
