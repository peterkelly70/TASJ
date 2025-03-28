"""Theme Controller for TASJ Application.

This module provides the controller layer for theme management, coordinating
between the theme model and UI components. It handles:
- Theme application to widgets
- Font management for themes
- Theme-specific styling

The controller maintains the current application state regarding themes and
coordinates with the font controller for font management.

Example usage:
```python
theme_controller = ThemeController(font_controller)
theme_controller.apply_theme("dark", main_window)
theme_controller.set_custom_font(custom_font)
```

Classes:
    ThemeController: Core class for theme management logic
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont
from model.theme_model import ThemeModel
from controller.font_controller import FontController

logger = logging.getLogger(__name__)

class ThemeController:
    """Controller for managing application themes.
    
    This class coordinates theme operations between the model and view layers,
    including:
    - Theme selection and application
    - Font management for themes
    - Theme-specific widget styling
    
    The controller maintains theme state and coordinates with the font controller
    for font-related operations.
    
    Attributes:
        model (ThemeModel): The theme data model
        font_controller (FontController): Controller for font operations
        current_font (Optional[QFont]): Currently active font
    """
    
    def __init__(self, font_controller: FontController) -> None:
        """Initialize the theme controller.
        
        Args:
            font_controller (FontController): Controller for font operations
        """
        self.model = ThemeModel()
        self.font_controller = font_controller
        self.current_font: Optional[QFont] = None
        
    def get_available_themes(self) -> list[str]:
        """Get list of available themes.
        
        Delegates to the model to get available themes.
        
        Returns:
            list[str]: Sorted list of available theme names
        """
        return self.model.get_available_themes()
        
    def load_stylesheet(self, theme_name: str) -> str:
        """Load the stylesheet for a given theme name."""
        return self.model.load_stylesheet(theme_name)

    def apply_theme(self, theme_name: str, target: QWidget) -> None:
        """Apply a theme to a widget.
        
        Coordinates the application of theme styles and fonts to a widget
        and its children. If no custom font is set, attempts to load and
        apply the theme's default font.
        
        Args:
            theme_name (str): Name of the theme to apply
            target (QWidget): Widget to apply the theme to
            
        The method will:
        1. Load theme data from the model
        2. Apply stylesheet if available
        3. Handle font loading and application
        4. Apply theme to all child widgets
        """
        # Load theme data
        theme_data = self.model.load_theme(theme_name)
        if not theme_data:
            return
            
        # Apply stylesheet
        if 'stylesheet' in theme_data:
            logger.info(f"Applying stylesheet for theme: {theme_name}")
            target.setStyleSheet(theme_data['stylesheet'])
            logger.debug(f"Applied stylesheet:\n{theme_data['stylesheet']}")
        else:
            logger.warning(f"No stylesheet found for theme: {theme_name}")
            
        # Handle font if no custom font is set
        if not self.current_font:
            theme_font_id = self.model.get_theme_font_id(theme_name)
            self.current_font = self.font_controller.ensure_font_available(theme_font_id, target)
            if not self.current_font:
                # Fallback to system font if download failed or was declined
                self.current_font = QFont("DejaVu Sans", 10)
                
        # Apply font
        target.setFont(self.current_font)
        for widget in target.findChildren(QWidget):
            widget.setFont(self.current_font)
            
    def set_custom_font(self, font: QFont) -> None:
        """Set a custom font override.
        
        Overrides the theme's default font with a custom selection.
        
        Args:
            font (QFont): The custom font to use
            
        Note: This font will be used instead of theme-specific fonts
        until it is cleared or the application is restarted.
        """
        self.current_font = font
