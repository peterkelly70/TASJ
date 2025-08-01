import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

from model.traveller_map_api import TravellerMapAPI
from view.loading_overlay_widget import LoadingOverlayWidget

logger = logging.getLogger(__name__)

class SectorMapWidget(QWidget):
    """Widget for displaying the sector map using the Traveller Map API."""
    
    system_selected = pyqtSignal(dict)
    map_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.systems = []
        self.selected_system = None
        self.sector_name = None
        self.map_pixmap = None
        self.loading_error = False
        self.error_message = ""
        self.loader_thread = None
        self.current_milieu = "M1105"  # Default milieu
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlayWidget(self, "Loading sector map...")
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
        
    def set_systems(self, systems: List[Dict[str, Any]]):
        """Set the systems to display on the map."""
        self.systems = systems
        self.update()
        
    def set_sector(self, sector: Dict[str, Any], milieu: Optional[str] = None):
        """Set the current sector and load its map from the API.
        
        Args:
            sector: Dictionary containing sector data
            milieu: Optional milieu code to use for sector data
        """
        if not sector:
            return
            
        # Get sector name
        self.sector_name = sector.get('name')
        if not self.sector_name:
            self.map_error.emit("No sector name provided")
            return
            
        # Set milieu if provided
        if milieu:
            self.current_milieu = milieu
        
        # Show loading overlay
        self.loading_overlay.set_message(f"Loading map for {self.sector_name}...")
        self.loading_overlay.show_loading()
        
        # Reset any previous errors
        self.loading_error = False
        self.error_message = ""
        
        # Load sector map from API
        try:
            # Get sector map from API - returns (pixmap, error_message) tuple
            pixmap, error = self.api.get_sector_map(self.sector_name, self.current_milieu)
            
            # Hide loading overlay
            self.loading_overlay.hide_loading()
            
            if pixmap:
                # Use the pixmap directly
                self.map_pixmap = pixmap
                self.update()
            else:
                self.loading_error = True
                self.error_message = error or f"Failed to load map for sector {self.sector_name}"
                self.map_error.emit(self.error_message)
        except Exception as e:
            # Hide loading overlay
            self.loading_overlay.hide_loading()
            
            self.loading_error = True
            self.error_message = f"Error loading map: {str(e)}"
            self.map_error.emit(self.error_message)
            logger.error(f"Error loading sector map: {e}")
            
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
            # Check if a system was clicked
            if self.map_pixmap and self.systems:
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
                    # Find closest system
                    closest_system = None
                    closest_distance = float('inf')
                    
                    for system in self.systems:
                        # Get system position
                        system_x = system.get('x', 0)
                        system_y = system.get('y', 0)
                        
                        # Calculate distance
                        distance = ((system_x - map_x) ** 2 + (system_y - map_y) ** 2) ** 0.5
                        
                        # Update closest system if this one is closer
                        if distance < closest_distance:
                            closest_system = system
                            closest_distance = distance
                    
                    # Check if system is close enough to click
                    if closest_system and closest_distance < 20:  # Adjust threshold as needed
                        self.selected_system = closest_system
                        self.update()
                        self.system_selected.emit(closest_system)
            
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
        """Paint the sector map."""
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
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a sector to view its map")
            return
            
        # Calculate map dimensions with zoom
        map_width = self.map_pixmap.width() * self.zoom_factor
        map_height = self.map_pixmap.height() * self.zoom_factor
        
        # Calculate offset to center the map
        offset_x = (self.width() - map_width) / 2 + self.pan_offset_x
        offset_y = (self.height() - map_height) / 2 + self.pan_offset_y
        
        # Draw map - convert float coordinates to integers for drawPixmap
        painter.drawPixmap(int(offset_x), int(offset_y), int(map_width), int(map_height), self.map_pixmap)
        
        # Draw systems if available
        if self.systems:
            for system in self.systems:
                # Get system position
                system_x = system.get('x', 0)
                system_y = system.get('y', 0)
                
                # Calculate screen position
                screen_x = offset_x + system_x * self.zoom_factor
                screen_y = offset_y + system_y * self.zoom_factor
                
                # Draw system
                if system == self.selected_system:
                    # Highlight selected system
                    painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
                    painter.setBrush(QBrush(Qt.GlobalColor.yellow))
                    painter.drawEllipse(screen_x - 5, screen_y - 5, 10, 10)
                else:
                    # Draw normal system
                    painter.setPen(QPen(Qt.GlobalColor.white, 1))
                    painter.setBrush(QBrush(Qt.GlobalColor.white))
                    painter.drawEllipse(screen_x - 3, screen_y - 3, 6, 6)
