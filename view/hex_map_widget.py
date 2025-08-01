import sys
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

from PyQt6.QtWidgets import (
    QWidget, QMenu, QInputDialog, QMessageBox, QApplication, 
    QMainWindow, QVBoxLayout, QDialog, QFormLayout, QLineEdit, 
    QComboBox, QTextEdit, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QFontMetrics, 
    QPainterPath, QPixmap, QPaintEvent, QBrush, QImage
)

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

# Using Planet class from model.planet instead of System
# JumpRoute functionality will be handled with a simple dictionary for now
from model.planet import Planet

# Define a simple JumpRoute class since it's not in the model
class JumpRoute:
    def __init__(self, from_system_id: int, to_system_id: int, jump_distance: int = 1):
        self.from_system_id = from_system_id
        self.to_system_id = to_system_id
        self.jump_distance = jump_distance

# Using existing Sector class from traveller_map_api
from model.traveller_map_api import TravellerMapAPI
from utils.sector_map_loader import SectorMapLoader


class HexMapWidget(QWidget):
    """Interactive hex map widget for displaying Traveller sector maps."""
    
    # Signals
    system_selected = pyqtSignal(dict)
    system_updated = pyqtSignal(dict)
    system_deleted = pyqtSignal(dict)
    map_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        
        # Map state
        self.systems = []
        self.selected_system = None
        self.current_sector = None
        self.current_milieu = "M1105"  # Default milieu
        
        # Image display properties
        self.map_pixmap = None
        self.map_rect = QRectF()
        self.map_scale = 1.0
        
        # Zoom and pan
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.max_zoom = 3.0
        self.min_zoom = 0.5
        self.pan_offset = QPointF(0, 0)
        self.panning = False
        self.last_pan_pos = None
        
        # Sector map loader
        self.map_loader = SectorMapLoader()
        
        # Enable mouse tracking for panning
        self.setMouseTracking(True)
        
    def set_systems(self, systems: List[Dict[str, Any]]):
        """Set the systems to display on the map."""
        self.systems = systems
        self.update()
        
    def set_sector(self, sector: Dict[str, Any], milieu: Optional[str] = None):
        """Set the current sector and load its map from the API."""
        self.current_sector = sector
        
        # Set milieu if provided
        if milieu:
            self.current_milieu = milieu
        
        # If no sector is provided, clear the display
        if not sector:
            self.map_pixmap = None
            self.update()
            return
            
        # Load the sector map
        self._load_sector_map(sector['name'] if isinstance(sector, dict) else str(sector))
    
    def _load_sector_map(self, sector_name: str):
        """Load a sector map from the API or cache."""
        map_path = self.map_loader.get_sector_map_path(sector_name, self.current_milieu)
        if map_path and os.path.exists(map_path):
            self.map_pixmap = QPixmap(map_path)
            self._center_map()
            self.update()
    
    def _center_map(self):
        """Center the map in the widget."""
        if not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        # Reset zoom and center the map
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self._update_map_rect()
    
    def _update_map_rect(self):
        """Update the map rectangle based on zoom and pan."""
        if not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        # Calculate scaled size
        scaled_size = self.map_pixmap.size() * self.zoom_factor
        
        # Calculate position to center the map
        x = (self.width() - scaled_size.width()) / 2 + self.pan_offset.x()
        y = (self.height() - scaled_size.height()) / 2 + self.pan_offset.y()
        
        self.map_rect = QRectF(x, y, scaled_size.width(), scaled_size.height())
        
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        if not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        # Get mouse position relative to the widget
        mouse_pos = event.position()
        
        # Calculate zoom factor
        zoom_delta = event.angleDelta().y() * 0.001
        new_zoom = self.zoom_factor * (1.0 + zoom_delta)
        
        # Clamp zoom factor to reasonable limits
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        if new_zoom != self.zoom_factor:
            # Calculate the position in map coordinates before zooming
            map_pos = (mouse_pos - self.map_rect.topLeft()) / self.zoom_factor
            
            # Update zoom factor
            old_zoom = self.zoom_factor
            self.zoom_factor = new_zoom
            
            # Adjust pan offset to zoom toward mouse position
            new_map_pos = map_pos * self.zoom_factor
            delta = new_map_pos - (mouse_pos - self.map_rect.topLeft())
            self.pan_offset += delta / old_zoom
            
            self._update_map_rect()
            self.update()
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self.panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            # Handle system selection
            pos = event.position()
            
            # Convert to map coordinates
            if self.map_rect.contains(pos):
                # Find the closest system within a reasonable distance
                closest_system = None
                min_distance = float('inf')
                
                for system in self.systems:
                    sys_pos = self._get_system_screen_pos(system, 0, 0, 0)
                    if not sys_pos:
                        continue
                        
                    distance = (pos - QPointF(*sys_pos)).manhattanLength()
                    if distance < 20 * self.zoom_factor and distance < min_distance:  # 20 pixels tolerance
                        min_distance = distance
                        closest_system = system
                
                if closest_system:
                    self.selected_system = closest_system
                    self.system_selected.emit(closest_system)
                    self.update()
                    return
            
            # If we get here, no system was clicked
            if self.selected_system:
                self.selected_system = None
                self.update()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning."""
        if not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        if self.panning and self.last_pan_pos:
            # Calculate pan delta
            delta = event.position() - self.last_pan_pos
            
            # Update pan offset
            self.pan_offset += delta
            
            # Update last position
            self.last_pan_pos = event.position()
            
            # Update map rectangle and redraw
            self._update_map_rect()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to end panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def resizeEvent(self, event):
        """Handle widget resize events."""
        super().resizeEvent(event)
        self._update_map_rect()
        self.update()
            
    def resetZoom(self):
        """Reset zoom and pan to default values."""
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self._update_map_rect()
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        """Handle paint events."""
        if not self.isVisible():
            return
            
        painter = QPainter(self)
        
        try:
            # Set up rendering hints
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            
            # Fill background with black
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            
            # Draw the sector map if available
            if self.map_pixmap and not self.map_pixmap.isNull():
                # Draw the map - ensure consistent rectangle types
                target_rect = self.map_rect.toRect() if hasattr(self.map_rect, 'toRect') else QRectF(self.map_rect).toRect()
                source_rect = self.map_pixmap.rect()
                painter.drawPixmap(target_rect, self.map_pixmap, source_rect)
                
                # Draw systems on top of the map
                self._draw_systems(painter)
                
                # Draw any debug info if needed
                if False:  # Set to True to enable debug info
                    debug_text = f"Zoom: {self.zoom_factor:.1f}x | "
                    debug_text += f"Pan: ({self.pan_offset.x():.0f}, {self.pan_offset.y():.0f})"
                    if self.current_sector:
                        sector_name = self.current_sector.get('name', 'Unknown') if isinstance(self.current_sector, dict) else str(self.current_sector)
                        debug_text += f" | Sector: {sector_name}"
                    
                    painter.setPen(Qt.GlobalColor.white)
                    painter.drawText(10, 20, debug_text)
            
        finally:
            # Make sure the painter is properly ended
            painter.end()
            
    def _draw_systems(self, painter: QPainter):
        """Draw all systems on the sector map."""
        if not self.systems or not self.map_pixmap or self.map_pixmap.isNull():
            return
            
        # Set up the pen for system markers
        pen = QPen(Qt.GlobalColor.white, 1.5 * self.zoom_factor)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        # Draw each system
        for system in self.systems:
            # Get screen position for this system
            pos = self._get_system_screen_pos(system)
            if not pos:
                continue
                
            # Check if the position is within the visible area
            if not self.rect().contains(pos.toPoint(), margin=20):
                continue
                
            # Set up the brush (red for selected, blue for others)
            if self._is_system_selected(system):
                brush = QBrush(Qt.GlobalColor.red)
            else:
                brush = QBrush(Qt.GlobalColor.blue)
                
            painter.setBrush(brush)
            
            # Draw the system marker (small circle)
            marker_radius = 4.0 * self.zoom_factor
            painter.drawEllipse(pos, marker_radius, marker_radius)
            
            # Draw the system name if zoomed in enough
            if self.zoom_factor > 0.8:
                name = system.get('name', 'Unknown')
                if name:
                    # Set up text
                    font = painter.font()
                    font.setPointSizeF(8.0 * self.zoom_factor)
                    painter.setFont(font)
                    
                    # Draw text with outline for better visibility
                    text_rect = QRectF(pos.x() + 8, pos.y() - 8, 100, 20)
                    
                    # Draw outline
                    outline_pen = QPen(Qt.GlobalColor.black, 2.0 * self.zoom_factor)
                    outline_pen.setCosmetic(True)
                    painter.setPen(outline_pen)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
                    
                    # Draw text
                    painter.setPen(Qt.GlobalColor.white)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
    
    def _draw_hex_grid(self, painter: QPainter):
        """Draw the hex grid with proper tessellation matching Traveller style."""
        # Set up pen for grid lines - thinner white lines
        pen = QPen(Qt.GlobalColor.white, 0.8, Qt.PenStyle.SolidLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        # Hex size and dimensions - slightly larger hexes
        self.hex_size = 24 * self.zoom_factor
        self.hex_width = 2 * self.hex_size
        self.hex_height = math.sqrt(3) * self.hex_size
        
        # Calculate visible area
        view_width = self.width()
        view_height = self.height()
        
        # Grid dimensions (Traveller standard)
        self.grid_cols = 32
        self.grid_rows = 40
        
        # Calculate grid dimensions in pixels
        grid_pixel_width = (self.grid_cols + 0.5) * self.hex_width * 0.75
        grid_pixel_height = (self.grid_rows + 1) * self.hex_height * 0.5
        
        # Calculate starting position (centered with some padding)
        self.grid_start_x = (view_width - grid_pixel_width) / 2 + self.pan_offset_x
        self.grid_start_y = (view_height - grid_pixel_height) / 2 + self.pan_offset_y
        
        # Draw a black background for the grid area
        grid_rect = QRectF(
            self.grid_start_x - self.hex_width,
            self.grid_start_y - self.hex_height,
            grid_pixel_width + 2 * self.hex_width,
            grid_pixel_height + 2 * self.hex_height
        )
        painter.fillRect(grid_rect, Qt.GlobalColor.black)
        
        # Draw hexagons
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                # Convert grid to pixel coordinates
                x, y = self._grid_to_pixel(col, row)
                
                # Only draw if visible
                if (x + self.hex_width > 0 and x - self.hex_width < view_width and 
                    y + self.hex_height > 0 and y - self.hex_height < view_height):
                    self._draw_hex(painter, x, y, self.hex_size * 0.9, fill=False)
    
    def _grid_to_pixel(self, col: int, row: int) -> tuple[float, float]:
        """Convert grid coordinates to pixel coordinates."""
        x = self.grid_start_x + col * self.hex_width * 0.75
        y = self.grid_start_y + row * self.hex_height * 0.5
        
        # Offset odd rows
        if row % 2 == 1:
            x += self.hex_width * 0.375
            
        # Draw hex coordinates (for debugging)
        if hasattr(self, 'debug_mode') and self.debug_mode and self.zoom_factor > 1.5:
            painter.drawText(QRectF(x - 20, y - 10, 40, 20),
                           Qt.AlignmentFlag.AlignCenter,
                           f"{col+1:02d}{row+1:02d}")
            
        return x, y
    
    def _draw_hex(self, painter: QPainter, center_x: float, center_y: float, size: float, fill: bool = False):
        """Draw a single hexagon with flat top orientation matching Traveller style."""
        hex_points = []
        for i in range(6):
            # Calculate points for a flat-topped hexagon
            angle_deg = 60 * i - 30  # Start at -30° for flat top
            angle_rad = math.radians(angle_deg)
            x = center_x + size * math.cos(angle_rad)
            y = center_y + size * math.sin(angle_rad)
            hex_points.append(QPointF(x, y))
        
        # Draw the hexagon with a slight fill color for better visibility
        if fill:
            painter.setBrush(QBrush(QColor(20, 20, 60)))  # Dark blue fill for selected hex
        else:
            painter.setBrush(QBrush(QColor(10, 10, 30)))  # Very dark background for empty hexes
        
        # Draw a slightly smaller hexagon for the fill to create a border effect
        if fill:
            inner_points = []
            for i in range(6):
                angle_deg = 60 * i - 30
                angle_rad = math.radians(angle_deg)
                x = center_x + (size * 0.9) * math.cos(angle_rad)  # Slightly smaller
                y = center_y + (size * 0.9) * math.sin(angle_rad)
                inner_points.append(QPointF(x, y))
            painter.drawPolygon(*inner_points)
        
        # Draw the hex border
        painter.drawPolygon(*hex_points)
        
    def _draw_jump_routes(self, painter: QPainter):
        """Draw jump routes between systems in Traveller style."""
        if not self.systems or len(self.systems) < 2:
            return
            
        # Set up pen for jump routes (light blue dotted lines with white outline)
        route_pen = QPen(QColor(150, 200, 255, 180), 1.2, Qt.PenStyle.DotLine)
        route_pen.setCosmetic(True)
        
        # Draw routes between systems that are within jump range
        for i, sys1 in enumerate(self.systems):
            pos1 = self._get_system_screen_pos(sys1, 0, 0, 0)  # Updated signature
            if not pos1:
                continue
                
            for sys2 in self.systems[i+1:]:
                pos2 = self._get_system_screen_pos(sys2, 0, 0, 0)  # Updated signature
                if not pos2:
                    continue
                    
                # Get hex coordinates for both systems
                hex1_x, hex1_y = self._get_system_coordinates(sys1)
                hex2_x, hex2_y = self._get_system_coordinates(sys2)
                
                if None in (hex1_x, hex1_y, hex2_x, hex2_y):
                    continue
                    
                # Convert to cube coordinates for distance calculation
                x1, z1 = int(hex1_x) - 1, int(hex1_y) - 1
                y1 = -x1 - z1
                x2, z2 = int(hex2_x) - 1, int(hex2_y) - 1
                y2 = -x2 - z2
                
                # Calculate hex distance
                dx = abs(x1 - x2)
                dy = abs(y1 - y2)
                dz = abs(z1 - z2)
                distance = (dx + dy + dz) / 2
                
                # Only draw routes for systems that are within 2 hexes of each other
                if 0 < distance <= 2:
                    # Draw white outline for better visibility
                    white_pen = QPen(Qt.GlobalColor.white, 2.5, Qt.PenStyle.DotLine)
                    white_pen.setCosmetic(True)
                    painter.setPen(white_pen)
                    painter.drawLine(QPointF(*pos1), QPointF(*pos2))
                    
                    # Draw the actual jump route
                    painter.setPen(route_pen)
                    painter.drawLine(QPointF(*pos1), QPointF(*pos2))
    
    def _get_system_screen_pos(self, system, hex_size=0, center_x=0, center_y=0):
        """Get screen coordinates for a system based on its hex coordinates."""
        try:
            # Get hex coordinates from system
            hex_x, hex_y = self._get_system_coordinates(system)
            if hex_x is None or hex_y is None:
                return None
                
            # Convert to numeric values
            try:
                hex_x = int(hex_x)
                hex_y = int(hex_y)
            except (ValueError, TypeError):
                return None
                
            # Calculate position based on hex coordinates
            # Adjust these calculations to match your sector map image's coordinate system
            hex_width = 40  # Adjust based on your map's hex size
            hex_height = math.sqrt(3) * hex_width / 2
            
            # Calculate pixel position (adjust as needed for your map)
            x = (hex_x - 1) * hex_width * 0.75
            y = (hex_y - 1) * hex_height
            
            # Offset odd rows
            if hex_y % 2 == 1:
                x += hex_width * 0.375
                
            # Apply zoom and pan
            x = x * self.zoom_factor + self.pan_offset.x() + (self.width() - self.map_rect.width()) / 2
            y = y * self.zoom_factor + self.pan_offset.y() + (self.height() - self.map_rect.height()) / 2
            
            return QPointF(x, y)
            
        except Exception as e:
            print(f"Error calculating system position: {e}")
            return None
    
    def _get_system_coordinates(self, system):
        """Extract and validate system coordinates."""
        hex_x = system.get('hex_x')
        hex_y = system.get('hex_y')
        
        # Fall back to x,y if hex_x/hex_y not available
        if not hex_x or not hex_y:
            hex_x = system.get('x')
            hex_y = system.get('y')
            if not hex_x or not hex_y:
                return None, None
                
        return hex_x, hex_y
    
    def _is_system_selected(self, system):
        """Check if the given system is currently selected."""
        return (self.selected_system and 
               system.get('name') == self.selected_system.get('name'))
    
    def _calculate_hex_position(self, x, y, hex_size, center_x, center_y):
        """Calculate the screen position for a hex at grid coordinates (x,y)."""
        hex_center_x = x * hex_size * 1.5 + center_x
        hex_center_y = y * hex_size * math.sqrt(3) + center_y
        
        # Offset every other row
        if y % 2 == 1:
            hex_center_x += hex_size * 0.75
            
        return hex_center_x, hex_center_y
    
    def _draw_system_marker(self, painter, x, y, hex_size):
        """Draw the marker for a system at the given position."""
        marker_radius = hex_size * 0.3
        painter.setPen(QPen(Qt.GlobalColor.cyan, 1.5))
        painter.setBrush(QBrush(Qt.GlobalColor.darkCyan))
        painter.drawEllipse(QPointF(x, y), marker_radius, marker_radius)
    
    def _draw_system_name(self, painter, system, x, y):
        """Draw the name of a system at the given position."""
        system_name = system.get('name', '???')
        if not system_name or system_name == '?????':  # Skip placeholder names
            return
            
        # Draw text background for better readability
        text_rect = QRectF(x - 40, y - 15, 80, 20)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.drawRoundedRect(text_rect, 3, 3)
        
        # Draw system name
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, system_name)
    
    def _draw_selected_highlight(self, painter, x, y, hex_size):
        """Draw a highlight around the selected system."""
        highlight_radius = hex_size * 0.5
        painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(x, y), highlight_radius, highlight_radius)
                
    def pixel_to_hex(self, x: float, y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to hex coordinates."""
        # Simple conversion for grid-based system
        zoomed_hex_width = self.hex_width * self.zoom_factor
        zoomed_hex_height = self.hex_height * self.zoom_factor
        
        hex_x = int((x - self.pan_offset_x) / zoomed_hex_width)
        hex_y = int((y - self.pan_offset_y) / zoomed_hex_height)
        
        return (hex_x, hex_y)
        
    def _find_system_at_hex(self, hex_coord: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """Find a system at the given hex coordinate."""
        hex_x, hex_y = hex_coord
        
        for system in self.systems:
            sys_x = system.get('x', 0)
            sys_y = system.get('y', 0)
            
            # Check if system is at this hex coordinate
            if sys_x == hex_x and sys_y == hex_y:
                return system
                
        return None
        
    def _show_context_menu(self, pos, hex_coord, system):
        """Show context menu for hex or system."""
        # This is a placeholder for the context menu implementation
        # In a full implementation, this would show a QMenu with options
        # like "Add System", "Edit System", "Delete System", etc.
        pass
