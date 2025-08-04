import logging
import math
import time
from typing import Dict, Any, List, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication, QToolButton, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint, QRectF, QPointF, QSize, QRect
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QBrush, QWheelEvent, 
    QMouseEvent, QFont, QLinearGradient, QPainterPath
)

from model.traveller_map_api import TravellerMapAPI
from view.loading_overlay_widget import LoadingOverlayWidget

logger = logging.getLogger(__name__)

class ViewMode:
    """View mode enumeration for the map widget."""
    GALACTIC = "galactic"
    SECTOR = "sector"
    SYSTEM = "system"


class SectorMapWidget(QWidget):
    """Widget for displaying the Traveller Map with multiple view modes.
    
    Features:
    - Galactic view: Overview of all sectors
    - Sector view: Detailed view of a single sector
    - System view: Close-up of a single system
    - Zoom and pan navigation
    - Click to select systems/sectors
    - Smooth transitions between views
    """
    
    system_selected = pyqtSignal(dict)
    sector_selected = pyqtSignal(dict)
    map_error = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)  # Emitted when view mode changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Map data
        self.systems = []
        self.sectors = []  # List of all sectors for galactic view
        self.current_sector = None  # Currently displayed sector (for sector view)
        self.selected_system = None
        self.highlighted_system = None
        self.highlighted_sector = None
        self.sector_name = None
        self.map_pixmap = None
        self.current_milieu = "M1105"  # Default milieu
        self.view_mode = ViewMode.GALACTIC  # Start in galactic view
        self.view_history = []  # For back navigation
        
        # View state
        self.zoom_level = 1.0
        self.min_zoom = 0.1  # Allow more zoom out for galactic view
        self.max_zoom = 4.0
        self.zoom_speed = 0.1
        self.pan_offset = QPointF(0, 0)
        self.pan_start = None
        self.sector_size = QSize(200, 160)  # Default size for sector boxes in galactic view
        self.sector_margin = 10  # Margin between sectors in galactic view
        
        # Visual settings
        self.cell_size = 30  # Base hex size in pixels at zoom 1.0
        self.margin = 50     # Margin around the map
        
        # Colors and styles
        self.sector_box_color = QColor(70, 130, 180, 180)  # Steel blue with transparency
        self.sector_highlight_color = QColor(100, 180, 255, 220)
        self.sector_selected_color = QColor(255, 215, 0, 220)  # Gold
        self.sector_border_color = QColor(30, 60, 90)
        self.sector_text_color = Qt.GlobalColor.white
        self.sector_font = QFont("Arial", 10, QFont.Weight.Bold)
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlayWidget(self, "Loading sector map...")
        self.loading_overlay.hide()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Create the API instance
        self.api = TravellerMapAPI()
        
        # Navigation controls
        self.back_button = QToolButton()
        self.back_button.setText("◀ Back")
        self.back_button.setVisible(False)
        self.back_button.clicked.connect(self._on_back_clicked)
        
        # Layout for controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.back_button)
        controls_layout.addStretch()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(controls_layout)
        layout.addStretch()
        
        # Set cursor for better UX
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Initialize with empty sector data
        self._load_initial_sectors()
        
    def _load_initial_sectors(self):
        """Load initial sector data for the galactic view."""
        try:
            from model.traveller_database import TravellerDatabase
            db = TravellerDatabase()
            
            # Get all sectors with their positions
            self.sectors = db.get_all_sectors()
            
            # If no sectors in DB, try to load from API
            if not self.sectors:
                logger.warning("No sectors found in database, loading from API...")
                self._load_sectors_from_api()
                
        except Exception as e:
            logger.error(f"Error loading sectors: {e}")
            self.sectors = []
            self.map_error.emit(f"Error loading sectors: {str(e)}")
    
    def _load_sectors_from_api(self):
        """Load sector data from the Traveller Map API."""
        try:
            # Get sector list from API
            sectors_data = self.api.get_sectors()
            
            # Transform to our format
            self.sectors = []
            for sector_data in sectors_data:
                self.sectors.append({
                    'name': sector_data.get('Name'),
                    'x': sector_data.get('X', 0),
                    'y': sector_data.get('Y', 0),
                    'milieu': sector_data.get('Milieu', self.current_milieu)
                })
                
            # Save to database for future use
            self._save_sectors_to_db()
            
        except Exception as e:
            logger.error(f"Error loading sectors from API: {e}")
            self.sectors = []
            raise
    
    def _save_sectors_to_db(self):
        """Save loaded sectors to the database."""
        if not self.sectors:
            return
            
        try:
            from model.traveller_database import TravellerDatabase
            db = TravellerDatabase()
            
            for sector in self.sectors:
                db.upsert_sector(
                    name=sector['name'],
                    x=sector.get('x', 0),
                    y=sector.get('y', 0),
                    milieu=sector.get('milieu', self.current_milieu)
                )
                
        except Exception as e:
            logger.error(f"Error saving sectors to database: {e}")
        
    def set_view_mode(self, mode: str, **kwargs):
        """Switch between different view modes.
        
        Args:
            mode: One of ViewMode.GALACTIC, ViewMode.SECTOR, or ViewMode.SYSTEM
            **kwargs: Additional arguments for the view mode
                     - For SECTOR: sector=dict
                     - For SYSTEM: system=dict, sector=dict
        """
        if mode not in [ViewMode.GALACTIC, ViewMode.SECTOR, ViewMode.SYSTEM]:
            logger.warning(f"Invalid view mode: {mode}")
            return
            
        # Save current view state if we're switching from a detailed view
        if self.view_mode in [ViewMode.SECTOR, ViewMode.SYSTEM]:
            self.view_history.append({
                'mode': self.view_mode,
                'sector': self.current_sector,
                'system': self.selected_system,
                'zoom': self.zoom_level,
                'pan': self.pan_offset
            })
        
        # Update view mode
        self.view_mode = mode
        self.back_button.setVisible(len(self.view_history) > 0)
        
        # Initialize the new view
        if mode == ViewMode.GALACTIC:
            self._setup_galactic_view()
        elif mode == ViewMode.SECTOR:
            self._setup_sector_view(kwargs.get('sector'))
        elif mode == ViewMode.SYSTEM:
            self._setup_system_view(kwargs.get('system'), kwargs.get('sector'))
            
        self.view_mode_changed.emit(mode)
        self.update()
        
    def _setup_galactic_view(self):
        """Initialize the galactic view."""
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self.current_sector = None
        self.selected_system = None
        self.loading_overlay.hide_loading()
        
    def _setup_sector_view(self, sector: Dict[str, Any]):
        """Initialize the sector view.
        
        Args:
            sector: Dictionary containing sector data
        """
        if not sector:
            logger.error("No sector provided for sector view")
            return
            
        self.current_sector = sector
        self.sector_name = sector.get('name')
        self.loading_overlay.show_loading(f"Loading {self.sector_name}...")
        
        # Load sector data asynchronously
        self._load_sector_data(sector)
        
    def _setup_system_view(self, system: Dict[str, Any], sector: Dict[str, Any]):
        """Initialize the system view.
        
        Args:
            system: Dictionary containing system data
            sector: Dictionary containing sector data
        """
        if not system or not sector:
            logger.error("System or sector data missing for system view")
            return
            
        self.current_sector = sector
        self.selected_system = system
        self.sector_name = sector.get('name')
        self.zoom_level = 2.0  # Start zoomed in on the system
        
        # Center on the selected system
        if 'x' in system and 'y' in system:
            self.pan_offset = QPointF(
                -system['x'] * self.zoom_level + self.width() / 2,
                -system['y'] * self.zoom_level + self.height() / 2
            )
            
        # Load detailed system data if needed
        self._load_system_data(system, sector)
        
    def _on_back_clicked(self):
        """Handle back button click for navigation."""
        if not self.view_history:
            return
            
        # Restore previous view state
        prev_view = self.view_history.pop()
        self.back_button.setVisible(len(self.view_history) > 0)
        
        if prev_view['mode'] == ViewMode.SECTOR:
            self.set_view_mode(ViewMode.SECTOR, sector=prev_view['sector'])
        elif prev_view['mode'] == ViewMode.GALACTIC:
            self.set_view_mode(ViewMode.GALACTIC)
            
    def _load_sector_data(self, sector: Dict[str, Any]):
        """Load data for a specific sector.
        
        Args:
            sector: Dictionary containing sector data
        """
        if not sector:
            logger.error("No sector provided for data loading")
            self.loading_overlay.hide_loading()
            return
            
        self.loading_overlay.show_loading(f"Loading {sector.get('name', 'sector')}...")
        
        try:
            # Load sector data from the database
            from model.traveller_database import TravellerDatabase
            db = TravellerDatabase()
            
            # Get systems for this sector
            self.systems = db.get_systems_by_sector(sector.get('name'))
            
            # Load the sector map
            self.map_pixmap, error = self.api.get_sector_map(
                sector.get('name'), 
                self.current_milieu
            )
            
            if not self.map_pixmap:
                raise Exception(error or "Failed to load sector map")
                
            self.loading_overlay.hide_loading()
            self.update()
            
        except Exception as e:
            logger.error(f"Error loading sector data: {e}")
            self.loading_overlay.hide_loading()
            self.map_error.emit(f"Failed to load sector: {str(e)}")
            # Fall back to empty data
            self.systems = []
            self.map_pixmap = None
        
    def _load_system_data(self, system: Dict[str, Any], sector: Dict[str, Any]):
        """Load detailed data for a specific system.
        
        Args:
            system: Dictionary containing system data
            sector: Dictionary containing sector data
        """
        if not system or not sector:
            logger.error("System or sector data missing")
            return
            
        try:
            # Load additional system details from database
            from model.traveller_database import TravellerDatabase
            db = TravellerDatabase()
            
            # Get detailed system info
            system_details = db.get_system_details(
                system.get('name'), 
                sector.get('name')
            )
            
            if system_details:
                # Update system with additional details
                system.update(system_details)
                
                # Load any planets for this system
                system['planets'] = db.get_planets_for_system(
                    system.get('name'), 
                    sector.get('name')
                )
                
                logger.debug(f"Loaded system details: {system.get('name')}")
                
        except Exception as e:
            logger.error(f"Error loading system data: {e}")
            # Continue with basic system data if detailed load fails
            
    def _get_sector_rect(self, sector: Dict[str, Any]) -> QRectF:
        """Get the rectangle for a sector in galactic view.
        
        Args:
            sector: Dictionary with sector data including 'x' and 'y' coordinates
                
        Returns:
            QRectF representing the sector's position and size in the view,
            or None if sector data is invalid
        """
        if not sector or 'x' not in sector or 'y' not in sector:
            return None
                
        # Calculate position based on sector coordinates
        # Each sector is 200x200 pixels with 10px margin
        try:
            x = float(sector.get('x', 0)) * 210 + self.pan_offset.x()
            y = float(sector.get('y', 0)) * 210 + self.pan_offset.y()
                
            # Apply zoom
            x = x * self.zoom_level + self.width() / 2
            y = y * self.zoom_level + self.height() / 2
            size = 200 * self.zoom_level
                
            return QRectF(x, y, size, size)
                
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid sector coordinates in {sector.get('name', 'unknown')}: {e}")
            return None
            
    def set_systems(self, systems: List[Dict[str, Any]]):
        """Set the systems to display on the map."""
        self.systems = systems
        self.update()
            
    def zoom_to_sector(self, sector_name: str):
        """Zoom to the specified sector.
        
        Args:
            sector_name: Name of the sector to zoom to
        """
        if not sector_name:
            logger.warning("No sector name provided to zoom_to_sector")
            return
            
        logger.debug(f"Zooming to sector: {sector_name}")
        
        # Find the sector in our list
        sector = next((s for s in self.sectors if s.get('name') == sector_name), None)
        if not sector:
            logger.warning(f"Sector not found: {sector_name}")
            return
            
        # If we're already in sector view for this sector, just center it
        if self.view_mode == ViewMode.SECTOR and self.sector_name == sector_name:
            self.center_on_sector(sector)
            return
            
        # Add current view to history before changing
        self._add_to_view_history()
        
        # Update selected sector
        self.selected_sector = sector_name
        self.sector_name = sector_name
        self.selected_system = None
        
        # Load sector data if needed
        if not self.map_pixmap or self.sector_name != sector_name:
            self._load_sector_data(sector)
        else:
            # Switch to sector view
            self.set_view_mode(ViewMode.SECTOR, sector=sector)
            
        # Center the view on this sector
        self.center_on_sector(sector)
        
        # Emit signal that sector was selected
        self.sector_selected.emit(sector_name)
        
    def zoom_to_system(self, system_name: str, sector_name: str = None):
        """Zoom to the specified system.
        
        Args:
            system_name: Name of the system to zoom to
            sector_name: Optional sector name if known
        """
        if not system_name:
            logger.warning("No system name provided to zoom_to_system")
            return
            
        logger.debug(f"Zooming to system: {system_name} in sector: {sector_name or 'current'}")
        
        # If sector is not provided, use the current sector
        if not sector_name and self.sector_name:
            sector_name = self.sector_name
            
        if not sector_name:
            logger.warning("No sector specified for system zoom")
            return
            
        # Find the sector
        sector = next((s for s in self.sectors if s.get('name') == sector_name), None)
        if not sector:
            logger.warning(f"Sector not found: {sector_name}")
            return
            
        # If we're not already in sector view for this sector, switch to it first
        if self.view_mode != ViewMode.SECTOR or self.sector_name != sector_name:
            self.zoom_to_sector(sector_name)
            
        # Find the system in the current sector
        system = next((s for s in (self.systems or []) 
                      if s.get('name') == system_name), None)
                      
        if not system:
            logger.warning(f"System {system_name} not found in sector {sector_name}")
            return
            
        # Add current view to history before changing
        self._add_to_view_history()
        
        # Update selected system
        self.selected_system = system
        
        # Switch to system view
        self.set_view_mode(ViewMode.SYSTEM, system=system, sector=sector)
        
        # Center the view on this system
        self.center_on_system(system)
        
        # Emit signal that system was selected
        self.system_selected.emit(system_name, sector_name)
    
    def center_on_sector(self, sector: Dict[str, Any]):
        """Center the view on the specified sector.
        
        Args:
            sector: Dictionary containing sector data with 'x' and 'y' coordinates
        """
        if not sector:
            logger.warning("No sector provided to center_on_sector")
            return
            
        # Calculate the position of the sector in the view
        rect = self._get_sector_rect(sector)
        if not rect:
            logger.warning(f"Could not get rect for sector: {sector.get('name')}")
            return
            
        # Calculate the offset needed to center the sector
        view_center = QPointF(self.width() / 2, self.height() / 2)
        sector_center = rect.center()
        
        # Update pan offset to center the sector
        self.pan_offset = view_center - sector_center
        
        # Update the display
        self.update()
    
    def center_on_system(self, system: Dict[str, Any]):
        """Center the map on the specified system.
        
        Args:
            system: Dictionary containing system data with 'x' and 'y' coordinates
        """
        if not system:
            logger.warning("No system provided to center_on_system")
            return
            
        try:
            # Get system coordinates
            system_x = float(system.get('x', 0))
            system_y = float(system.get('y', 0))
            
            # Calculate the offset needed to center the system
            view_center = QPointF(self.width() / 2, self.height() / 2)
            system_pos = QPointF(system_x, system_y) * self.zoom_level
            
            # Update pan offset to center the system
            self.pan_offset = view_center - system_pos
            
            # Update the display
            self.update()
            
        except (TypeError, ValueError) as e:
            logger.error(f"Error centering on system {system.get('name')}: {e}")
    
    def _add_to_view_history(self):
        """Add current view to navigation history."""
        if self.view_mode == ViewMode.GALACTIC:
            self.view_history.append((ViewMode.GALACTIC, None, None))
        elif self.view_mode == ViewMode.SECTOR and self.current_sector:
            self.view_history.append((ViewMode.SECTOR, self.current_sector.get('name'), None))
        elif self.view_mode == ViewMode.SYSTEM and self.selected_system and self.current_sector:
            self.view_history.append((
                ViewMode.SYSTEM, 
                self.current_sector.get('name'),
                self.selected_system.get('name')
            ))
            
        # Limit history size
        if len(self.view_history) > 10:
            self.view_history.pop(0)
            
    def resetZoom(self):
        """Reset zoom and pan to default values."""
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self.update()
        
    def _draw_galactic_view(self, painter: QPainter):
        """Draw the galactic view with all sectors."""
        # Draw sector grid first
        self._draw_sector_grid(painter)
        
        # Then draw sector boxes
        for sector in self.sectors:
            self._draw_sector_box(painter, sector)
            
    def _draw_sector_grid(self, painter: QPainter):
        """Draw the grid lines between sectors in galactic view."""
        if not self.sectors:
            return
            
        # Find the bounds of all sectors
        x_coords = [s.get('x', 0) for s in self.sectors]
        y_coords = [s.get('y', 0) for s in self.sectors]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Set up pen for grid lines
        grid_pen = QPen(QColor(100, 100, 150, 100), 1.0, Qt.PenStyle.DotLine)
        painter.setPen(grid_pen)
        
        # Draw vertical grid lines
        for x in range(int(min_x), int(max_x) + 2):
            rect = self._get_sector_rect({'x': x, 'y': min_y})
            if rect:
                x_pos = rect.left()
                painter.drawLine(
                    int(x_pos), 
                    int(rect.top() - 1000),  # Extend beyond visible area
                    int(x_pos),
                    int(rect.bottom() + 1000)
                )
        
        # Draw horizontal grid lines
        for y in range(int(min_y), int(max_y) + 2):
            rect = self._get_sector_rect({'x': min_x, 'y': y})
            if rect:
                y_pos = rect.top()
                painter.drawLine(
                    int(rect.left() - 1000),  # Extend beyond visible area
                    int(y_pos),
                    int(rect.right() + 1000),
                    int(y_pos)
                )
    
    def _draw_sector_box(self, painter: QPainter, sector: Dict[str, Any]):
        """Draw a single sector box in the galactic view."""
        rect = self._get_sector_rect(sector)
        if not rect or not rect.isValid():
            return
            
        # Determine if this sector is selected or hovered
        is_selected = (self.selected_sector == sector.get('name') and 
                      self.view_mode == ViewMode.GALACTIC)
        is_hovered = (self.hovered_sector == sector.get('name') and 
                     self.view_mode == ViewMode.GALACTIC)
        
        # Set up colors based on state
        if is_selected:
            fill_color = self.sector_selected_color
        elif is_hovered:
            fill_color = self.sector_highlight_color
        else:
            fill_color = self.sector_box_color
            
        # Draw the sector box with shadow
        shadow_rect = rect.adjusted(2, 2, 2, 2)
        shadow_color = QColor(0, 0, 0, 50)
        
        # Draw shadow
        shadow_path = QPainterPath()
        radius = 5.0
        shadow_path.addRoundedRect(shadow_rect, radius, radius)
        painter.fillPath(shadow_path, shadow_color)
        
        # Draw main box with gradient
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, fill_color.lighter(120))
        gradient.setColorAt(1, fill_color.darker(120))
        
        painter.setPen(QPen(self.sector_border_color, 1.5))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)
        
        # Draw sector name
        painter.setPen(QPen(self.sector_text_color, 1))
        painter.setFont(self.sector_font)
        
        # Use abbreviation if available, otherwise use first part of name
        name = sector.get('abbreviation', sector.get('name', 'Unknown').split()[0])
        text_rect = rect.adjusted(5, 5, -5, -5)
        painter.drawText(text_rect, 
                        Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, 
                        name)
                        
        # Add subtle highlight at top for 3D effect
        if is_selected or is_hovered:
            highlight = QLinearGradient(rect.topLeft(), rect.topLeft() + QPointF(0, rect.height()/3))
            highlight.setColorAt(0, QColor(255, 255, 255, 40))
            highlight.setColorAt(1, Qt.GlobalColor.transparent)
            painter.fillPath(path, QBrush(highlight))
    
    def paintEvent(self, event):
        """Paint the map with current zoom and pan, handling different view modes."""
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | 
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
            
        # Fill background
        painter.fillRect(self.rect(), QColor(40, 44, 52))  # Dark theme background
            
        # Save painter state
        painter.save()
            
        try:
            # Apply zoom and pan
            painter.translate(self.pan_offset.x(), self.pan_offset.y())
            painter.scale(self.zoom_level, self.zoom_level)
                
            # Draw content based on current view mode
            if self.view_mode == ViewMode.GALACTIC:
                self._draw_galactic_view(painter)
            elif self.view_mode == ViewMode.SECTOR:
                self._draw_sector_view(painter)
            elif self.view_mode == ViewMode.SYSTEM:
                self._draw_system_view(painter)
                    
        finally:
            # Restore painter state
            painter.restore()
    
    def _draw_sector_view(self, painter: QPainter):
        """Draw the detailed sector view."""
        if not self.map_pixmap:
            return
            
        # Draw the sector map
        map_rect = QRectF(
            -self.map_pixmap.width() / 2,
            -self.map_pixmap.height() / 2,
            self.map_pixmap.width(),
            self.map_pixmap.height()
        )
        painter.drawPixmap(map_rect, self.map_pixmap, self.map_pixmap.rect())
        
        # Draw systems if available
        if self.systems:
            self._draw_systems(painter, map_rect.topLeft())
    
    def _draw_system_view(self, painter: QPainter):
        """Draw the detailed system view."""
        if not self.selected_system or not self.map_pixmap:
            return
            
        # Draw the sector map in the background (faded)
        painter.save()
        painter.setOpacity(0.3)
        self._draw_sector_view(painter)
        painter.restore()
        
        # Get system position relative to the sector
        system_x = self.selected_system.get('x', 0)
        system_y = self.selected_system.get('y', 0)
        
        # Draw a circle around the selected system
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(system_x, system_y), 20, 20)
        
        # Draw system name
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # Draw name with background for better visibility
        name = self.selected_system.get('name', 'Unknown System')
        text_rect = painter.boundingRect(
            QRectF(system_x - 100, system_y - 50, 200, 20),
            Qt.AlignmentFlag.AlignCenter,
            name
        )
        
        # Add some padding
        text_rect.adjust(-5, -2, 5, 2)
        
        # Draw background
        painter.fillRect(text_rect, QColor(0, 0, 0, 180))
        
        # Draw text
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter,
            name
        )
        
        # Draw system details
        details = [
            f"UWP: {self.selected_system.get('uwp', '?')}",
            f"Bases: {', '.join(self.selected_system.get('bases', [])) or 'None'}",
            f"Travel Zone: {'Amber' if self.selected_system.get('amber_zone') else 'Green'}",
            f"Population: {self.selected_system.get('population', '?')}"
        ]
        
        # Draw details below the name
        y_offset = system_y + 40
        for detail in details:
            detail_rect = QRectF(system_x - 100, y_offset, 200, 20)
            text_rect = painter.boundingRect(
                detail_rect,
                Qt.AlignmentFlag.AlignCenter,
                detail
            )
            text_rect.adjust(-5, -2, 5, 2)
            
            # Draw background
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            
            # Draw text
            painter.drawText(
                detail_rect,
                Qt.AlignmentFlag.AlignCenter,
                detail
            )
            y_offset += 20
        
        painter.restore()
    
    def _draw_systems(self, painter: QPainter, offset: QPointF):
        """Draw systems on the map."""
        if not self.systems:
            return
            
        for system in self.systems:
            x = system.get('x', 0) - offset.x()
            y = system.get('y', 0) - offset.y()
            
            # Draw system marker
            if system == self.selected_system:
                painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
                painter.setBrush(QBrush(Qt.GlobalColor.yellow))
            elif system == self.highlighted_system:
                painter.setPen(QPen(Qt.GlobalColor.cyan, 2))
                painter.setBrush(QBrush(Qt.GlobalColor.cyan))
            else:
                painter.setPen(QPen(Qt.GlobalColor.white, 1))
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                
            painter.drawEllipse(QPointF(x, y), 3, 3)
    
    def _draw_debug_info(self, painter: QPainter):
        """Draw debug information on top of the map."""
        if not hasattr(self, 'debug_info') or not self.debug_info:
            return
            
        debug_text = f"View: {self.view_mode} | Zoom: {self.zoom_level:.1f}x | "
        debug_text += f"Pan: ({self.pan_offset.x():.0f}, {self.pan_offset.y():.0f})"
        
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(10, 20, debug_text)

    def mousePressEvent(self, event):
        """Handle mouse press events for selecting sectors and systems."""
        logger.debug(f"Mouse press at: {event.position().toPoint()}")
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert screen coordinates to map coordinates
            pos = event.position()
            map_pos = (pos - self.pan_offset) / self.zoom_level
            
            logger.debug(f"Map position: {map_pos}, Zoom: {self.zoom_level}, Pan: {self.pan_offset}")
            
            if self.view_mode == ViewMode.GALACTIC:
                logger.debug(f"Checking sectors in GALACTIC view. Total sectors: {len(self.sectors)}")
                # Check if a sector was clicked
                for sector in self.sectors:
                    rect = self._get_sector_rect(sector)
                    if rect:
                        logger.debug(f"Checking sector: {sector.get('name')} at {rect}")
                        if rect.contains(map_pos):
                            logger.info(f"Sector selected: {sector.get('name')}")
                            self.sector_selected.emit(sector)
                            self.update()
                            return
                        
            elif self.view_mode == ViewMode.SECTOR and self.systems:
                logger.debug(f"Checking systems in SECTOR view. Total systems: {len(self.systems)}")
                # Check if a system was clicked
                click_radius = 5 / self.zoom_level
                
                for system in self.systems:
                    system_pos = QPointF(system.get('x', 0), system.get('y', 0))
                    distance = (system_pos - map_pos).manhattanLength()
                    logger.debug(f"Checking system: {system.get('name')} at {system_pos}, distance: {distance}")
                    if distance < click_radius:
                        logger.info(f"System selected: {system.get('name')}")
                        self.system_selected.emit(system)
                        self.update()
                        return
        
        # Call parent class implementation for other mouse events
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover effects."""
        pos = event.position()
        map_pos = (pos - self.pan_offset) / self.zoom_level
        
        # Debug logging for mouse position
        if hasattr(self, 'last_debug_log') and (time.time() - self.last_debug_log) < 0.5:
            pass  # Limit debug logging rate
        else:
            logger.debug(f"Mouse move - Screen: {pos.toPoint()}, Map: {map_pos}")
            self.last_debug_log = time.time()
        
        if self.view_mode == ViewMode.GALACTIC:
            # Check for sector hover
            hovered_sector = None
            for sector in self.sectors:
                rect = self._get_sector_rect(sector)
                if rect and rect.contains(map_pos):
                    hovered_sector = sector
                    break
            
            if hovered_sector != self.highlighted_sector:
                logger.debug(f"Sector hover: {hovered_sector.get('name') if hovered_sector else 'None'}")
                self.highlighted_sector = hovered_sector
                self.setCursor(Qt.CursorShape.PointingHandCursor if hovered_sector 
                             else Qt.CursorShape.ArrowCursor)
                self.update()
                
        elif self.view_mode == ViewMode.SECTOR and self.systems:
            # Check for system hover
            hovered_system = None
            hover_radius = 5 / self.zoom_level
            
            for system in self.systems:
                system_pos = QPointF(system.get('x', 0), system.get('y', 0))
                distance = (system_pos - map_pos).manhattanLength()
                if distance < hover_radius:
                    hovered_system = system
                    break
            
            if hovered_system != self.highlighted_system:
                logger.debug(f"System hover: {hovered_system.get('name') if hovered_system else 'None'}")
                self.highlighted_system = hovered_system
                self.setCursor(Qt.CursorShape.PointingHandCursor if hovered_system 
                             else Qt.CursorShape.ArrowCursor)
                self.update()
        
        # Call parent class implementation for other mouse move events
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        # Reset any temporary states here if needed
        super().mouseReleaseEvent(event)
