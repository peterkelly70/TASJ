import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

from model.traveller_map_api import TravellerMapAPI
from view.loading_overlay_widget import LoadingOverlayWidget

logger = logging.getLogger(__name__)

class SystemMapWidget(QWidget):
    """Widget for displaying the system jump map using the Traveller Map API."""
    
    planet_selected = pyqtSignal(dict)
    map_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.planets = []
        self.selected_planet = None
        self.system_name = None
        self.sector_name = None
        self.map_pixmap = None
        self.loading_error = False
        self.error_message = ""
        self.loader_thread = None
        self.current_milieu = "M1105"  # Default milieu
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlayWidget(self, "Loading system map...")
        self.loading_overlay.hide()
        
        # Zoom related variables
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.max_zoom = 3.0
        self.min_zoom = 0.5
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.panning = False
        self.last_pan_pos = None
        
        # Enable mouse tracking for panning
        self.setMouseTracking(True)
        
        # Create the API instance
        self.api = TravellerMapAPI()
        
    def set_planets(self, planets: List[Dict[str, Any]]):
        """Set the planets to display on the map."""
        self.planets = planets
        self.update()
        
    def set_system(self, system: Dict[str, Any], milieu: Optional[str] = None):
        """Set the current system and load its map from the API.
        
        Args:
            system: Dictionary containing system data
            milieu: Optional milieu code to use for system data
        """
        if not system:
            return
            
        # Get system and sector names
        self.system_name = system.get('name')
        self.sector_name = system.get('sector_name')
        
        if not self.system_name or not self.sector_name:
            self.map_error.emit("System name or sector name missing")
            return
            
        # Set milieu if provided
        if milieu:
            self.current_milieu = milieu
        
        # Show loading overlay
        self.loading_overlay.set_message(f"Loading map for {self.system_name} system...")
        self.loading_overlay.show_loading()
        
        # Reset any previous errors
        self.loading_error = False
        self.error_message = ""
        
        # Load system map from API
        try:
            # Get system jump map from API - returns (pixmap, error_message) tuple
            pixmap, error = self.api.get_system_jump_map(self.sector_name, self.system_name, self.current_milieu)
            
            # Hide loading overlay
            self.loading_overlay.hide_loading()
            
            if pixmap:
                # Use the pixmap directly
                self.map_pixmap = pixmap
                self.update()
            else:
                self.loading_error = True
                self.error_message = error or f"Failed to load map for system {self.system_name} in sector {self.sector_name}"
                self.map_error.emit(self.error_message)
        except Exception as e:
            # Hide loading overlay
            self.loading_overlay.hide_loading()
            
            self.loading_error = True
            self.error_message = f"Error loading map: {str(e)}"
            self.map_error.emit(self.error_message)
            logger.error(f"Error loading system map: {e}")
            
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        # Calculate zoom delta based on wheel movement
        delta = event.angleDelta().y() / 120  # 120 units per step
        zoom_delta = delta * self.zoom_step
        
        # Apply zoom
        new_zoom = self.zoom_factor + zoom_delta
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        # Only update if zoom changed
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self.update()
            
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            # Start panning
            self.panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            # Check if a planet was clicked
            if self.map_pixmap and self.planets:
                # Calculate map position
                map_width = self.map_pixmap.width() * self.zoom_factor
                map_height = self.map_pixmap.height() * self.zoom_factor
                
                # Calculate offset to center the map
                offset_x = (self.width() - map_width) / 2 + self.pan_offset_x
                offset_y = (self.height() - map_height) / 2 + self.pan_offset_y
                
                # Calculate click position relative to map
                map_x = (event.position().x() - offset_x) / self.zoom_factor
                map_y = (event.position().y() - offset_y) / self.zoom_factor
                
                # Check if click is within map bounds
                if 0 <= map_x < self.map_pixmap.width() and 0 <= map_y < self.map_pixmap.height():
                    # Find closest planet
                    closest_planet = None
                    closest_distance = float('inf')
                    
                    for planet in self.planets:
                        # Get planet position
                        planet_x = planet.get('x', 0)
                        planet_y = planet.get('y', 0)
                        
                        # Calculate distance
                        distance = ((planet_x - map_x) ** 2 + (planet_y - map_y) ** 2) ** 0.5
                        
                        # Update closest planet if this one is closer
                        if distance < closest_distance:
                            closest_planet = planet
                            closest_distance = distance
                    
                    # Check if planet is close enough to click
                    if closest_planet and closest_distance < 20:  # Adjust threshold as needed
                        self.selected_planet = closest_planet
                        self.update()
                        self.planet_selected.emit(closest_planet)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning."""
        if self.panning and self.last_pan_pos:
            # Calculate pan delta
            delta_x = event.position().x() - self.last_pan_pos.x()
            delta_y = event.position().y() - self.last_pan_pos.y()
            
            # Update pan offset
            self.pan_offset_x += delta_x
            self.pan_offset_y += delta_y
            
            # Update last position
            self.last_pan_pos = event.position()
            
            # Redraw
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to end panning."""
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def resetZoom(self):
        """Reset zoom and pan to default values."""
        self.zoom_factor = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.update()
        
    def paintEvent(self, event):
        """Paint the system map."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Fill background
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        
        if self.loading_error:
            # Display error message
            painter.setPen(Qt.GlobalColor.red)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"Error: {self.error_message}")
            return
            
        if not self.map_pixmap:
            # Display loading message
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a system to view its map")
            return
            
        # Calculate map dimensions with zoom
        map_width = self.map_pixmap.width() * self.zoom_factor
        map_height = self.map_pixmap.height() * self.zoom_factor
        
        # Calculate offset to center the map
        offset_x = (self.width() - map_width) / 2 + self.pan_offset_x
        offset_y = (self.height() - map_height) / 2 + self.pan_offset_y
        
        # Draw map
        painter.drawPixmap(offset_x, offset_y, map_width, map_height, self.map_pixmap)
        
        # Draw planets if available
        if self.planets:
            for planet in self.planets:
                # Get planet position
                planet_x = planet.get('x', 0)
                planet_y = planet.get('y', 0)
                
                # Calculate screen position
                screen_x = offset_x + planet_x * self.zoom_factor
                screen_y = offset_y + planet_y * self.zoom_factor
                
                # Draw planet
                if planet == self.selected_planet:
                    # Highlight selected planet
                    painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
                    painter.setBrush(QBrush(Qt.GlobalColor.yellow))
                    painter.drawEllipse(screen_x - 5, screen_y - 5, 10, 10)
                else:
                    # Draw normal planet
                    painter.setPen(QPen(Qt.GlobalColor.white, 1))
                    painter.setBrush(QBrush(Qt.GlobalColor.white))
                    painter.drawEllipse(screen_x - 3, screen_y - 3, 6, 6)
