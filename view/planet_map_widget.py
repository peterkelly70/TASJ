import logging
from typing import Optional, Dict, Any
from urllib.parse import quote
import requests
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtGui import QPixmap, QPainter, QImage, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread

from model.planet_map_manager import PlanetMapManager
from model.traveller_map_api import TravellerMapAPI
from view.loading_overlay_widget import LoadingOverlayWidget

logger = logging.getLogger(__name__)

class PlanetMapWidget(QWidget):
    """Widget for displaying planet maps using TravellerWorlds.com API."""
    
    map_loaded = pyqtSignal(bool)  # Signal emitted when map is loaded (success/failure)
    map_error = pyqtSignal(str)   # Signal emitted when map loading fails with error message
    
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.planet_data = None
        self.map_pixmap = None
        self.db_path = db_path
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlayWidget(self, "Loading planet map...")
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
        
        # Initialize map manager if db_path is provided
        self.map_manager = None
        if db_path:
            self.set_db_path(db_path)
        
        self.setup_ui()
        
    def set_db_path(self, db_path):
        """Set the database path and initialize the map manager."""
        self.map_manager = PlanetMapManager(db_path)
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Map display label
        self.map_label = QLabel("No planet map available")
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setStyleSheet("background-color: #222; color: #ddd; border: 1px solid #444;")
        layout.addWidget(self.map_label)
        
        self.setLayout(layout)
    
    def set_planet(self, planet_data: Dict[str, Any]):
        """Set the planet data and attempt to load its map."""
        self.planet_data = planet_data
        if not planet_data:
            self.map_pixmap = None
            self.update()
            return
        self.load_map()
    
    def load_map(self):
        """Load the planet map from the database or generate a new one."""
        if not self.planet_data:
            self.map_label.setText("No planet selected")
            self.map_pixmap = None
            self.map_loaded.emit(False)
            return
        
        # Show loading overlay
        planet_name = self.planet_data.get('name', 'Unknown')
        self.loading_overlay.set_message(f"Loading map for {planet_name}...")
        self.loading_overlay.show_loading()
        
        # Check if map exists in database first
        map_data = self._get_map_from_database()
        
        if map_data:
            # Map exists in database, load it
            try:
                # Create QImage from binary data
                image = QImage()
                image.loadFromData(map_data)
                
                if image.isNull():
                    # Hide loading overlay
                    self.loading_overlay.hide_loading()
                    
                    error_msg = "Invalid image data from database"
                    logger.error(error_msg)
                    self.map_label.setText(f"Error: {error_msg}")
                    self.map_loaded.emit(False)
                    self.map_error.emit(error_msg)
                    return
                    
                # Convert to QPixmap for display
                pixmap = QPixmap.fromImage(image)
                self.map_pixmap = pixmap
                
                # Hide loading overlay
                self.loading_overlay.hide_loading()
                
                # Display the map
                self.update()
                self.map_loaded.emit(True)
                
            except Exception as e:
                # Hide loading overlay
                self.loading_overlay.hide_loading()
                
                error_msg = f"Error loading map from database: {str(e)}"
                logger.error(error_msg)
                self.map_label.setText(f"Error: {error_msg}")
                self.map_loaded.emit(False)
                self.map_error.emit(error_msg)
        else:
            # No map in database, generate a new one
            self.generate_new_map()
    
    def generate_new_map(self):
        """Generate a new map using the TravellerMap API."""
        if not self.planet_data:
            # Hide loading overlay if it's showing
            self.loading_overlay.hide_loading()
            return
            
        # Make sure loading overlay is showing
        planet_name = self.planet_data.get('name', 'Unknown')
        self.loading_overlay.set_message(f"Generating map for {planet_name}...")
        self.loading_overlay.show_loading()
            
        # Construct API URL
        api_url = self._construct_api_url()
        if not api_url:
            # Hide loading overlay
            self.loading_overlay.hide_loading()
            
            error_msg = "Could not construct API URL for planet map"
            logger.error(error_msg)
            self.map_label.setText(f"Error: {error_msg}")
            self.map_error.emit(error_msg)
            return
            
        # Download map asynchronously
        self._download_map_async()
    
    def _construct_api_url(self) -> str:
        """Construct the TravellerWorlds.com API URL for the current planet."""
        base_url = "https://travellerworlds.com/?"
        params = []
        
        # Add planet name
        name = self.planet_data.get("name", "")
        if name:
            params.append(f"name={quote(name)}")
        
        # Add UWP
        uwp = self.planet_data.get("UWP", "")
        if uwp:
            params.append(f"uwp={quote(uwp)}")
        
        # Add hex location if available
        hex_loc = self.planet_data.get("hex", "")
        if hex_loc:
            params.append(f"hex={quote(hex_loc)}")
        
        # Add sector if available
        sector = self.planet_data.get("sector", "")
        if sector:
            params.append(f"sector={quote(sector)}")
        
        # Add trade codes if available
        trade_codes = self.planet_data.get("trade_codes", [])
        for tc in trade_codes:
            params.append(f"tc={quote(tc)}")
        
        # Add other parameters if available
        for param in ["iX", "eX", "cX", "pbg", "popMulti", "belts", "gas_giants", 
                     "worlds", "bases", "travelZone", "nobz", "allegiance", "stellar"]:
            if param in self.planet_data:
                params.append(f"{param}={quote(str(self.planet_data[param]))}")
        
        # Add mapOnly parameter to get just the map
        params.append("mapOnly=1")
        
        # Construct the full URL
        url = base_url + "&".join(params)
        return url
    
    def _get_map_from_database(self) -> Optional[bytes]:
        """Get the map image data from the database if it exists."""
        if not self.map_manager or not self.planet_data or 'id' not in self.planet_data:
            return None
            
        try:
            # Get map data from database
            planet_id = self.planet_data['id']
            map_data = self.map_manager.get_map(planet_id)
            return map_data
        except Exception as e:
            logger.error(f"Error retrieving map from database: {e}")
            return None
    
    def _create_downloader_thread(self):
        """Create a thread for downloading planet maps."""
        class MapDownloaderThread(QThread):
            map_downloaded = pyqtSignal(bytes)
            download_failed = pyqtSignal(str)
            
            def __init__(self, url):
                super().__init__()
                self.url = url
                self.max_retries = 3
                self.retry_delay = 1.0  # seconds
                
            def run(self):
                try:
                    self._attempt_download()
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    logger.error(error_msg)
                    self.download_failed.emit(error_msg)
                    
            def _attempt_download(self):
                """Attempt to download the map with retries."""
                retry_count = 0
                error_msg = ""
                
                while retry_count < self.max_retries:
                    success, error_msg = self._download_single_attempt(retry_count)
                    if success:
                        return
                    
                    retry_count += 1
                    
                    # If we have more retries, wait before trying again
                    if retry_count < self.max_retries:
                        import time
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                    else:
                        self.download_failed.emit(error_msg)
                        
            def _download_single_attempt(self, retry_count):
                """Make a single download attempt."""
                try:
                    logger.info(f"Downloading planet map from: {self.url} (attempt {retry_count + 1}/{self.max_retries})")
                    response = requests.get(self.url, timeout=10)
                    
                    if response.status_code == 200:
                        # Get the image data
                        image_data = response.content
                        
                        # Verify it's a valid image
                        image = QImage()
                        if image.loadFromData(image_data):
                            self.map_downloaded.emit(image_data)
                            return True, ""
                        else:
                            error_msg = "Downloaded data is not a valid image"
                            logger.error(error_msg)
                            return False, error_msg
                    else:
                        error_msg = f"HTTP Error: {response.status_code}"
                        logger.error(error_msg)
                        return False, error_msg
                        
                except requests.exceptions.Timeout:
                    error_msg = "Connection timed out"
                    logger.error(error_msg)
                    return False, error_msg
                    
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"Connection error: {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg
                    
                except Exception as e:
                    error_msg = f"Error downloading planet map: {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg
                    
        return MapDownloaderThread(self.map_url)
        
    def _download_map_async(self):
        """Download the map from the API asynchronously."""
        # Clean up any existing thread
        if hasattr(self, 'downloader_thread') and self.downloader_thread and self.downloader_thread.isRunning():
            self.downloader_thread.quit()
            self.downloader_thread.wait()
        
        # Create and start the downloader thread
        self.downloader_thread = self._create_downloader_thread()
        self.downloader_thread.map_downloaded.connect(self._on_map_downloaded)
        self.downloader_thread.download_failed.connect(self._on_download_failed)
        self.downloader_thread.start()
        
    def _on_map_downloaded(self, image_data):
        """Handle successful map download."""
        # Hide loading overlay if it was showing during download
        self.loading_overlay.hide_loading()
        
        if self._save_map_to_database(image_data):
            self.load_map()  # Reload from database
        else:
            error_msg = f"Failed to save map for {self.planet_data.get('name', 'Unknown Planet')}"
            self.map_label.setText(error_msg)
            self.map_error.emit(error_msg)
            self.map_loaded.emit(False)
            self.map_error.emit(error_msg)
            
    def _on_download_failed(self, error_msg):
        """Handle failed map download."""
        # Hide loading overlay if it was showing during download
        self.loading_overlay.hide_loading()
        
        self.map_label.setText(f"Error: {error_msg}")
        self.map_loaded.emit(False)
        self.map_error.emit(error_msg)
    
    def _save_map_to_database(self, image_data):
        """Save the map image to the database."""
        if not self.map_manager or not self.planet_data:
            logger.error("Cannot save map: missing map manager or planet data")
            return False
            
        try:
            # Save map data to database
            planet_id = self.planet_data.get('id')
            if not planet_id:
                logger.error("Cannot save map: missing planet ID")
                return False
                
            success = self.map_manager.save_map(planet_id, image_data)
            if success:
                logger.info(f"Map saved to database for planet ID {planet_id}")
            else:
                logger.warning(f"Failed to save map for planet ID {planet_id}")
            return success
        except Exception as e:
            logger.error(f"Error saving map to database: {e}")
            return False
    
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
        """Handle mouse press events for panning."""
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.RightButton:
            # Start panning with middle or right mouse button
            self.panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        
        # Handle other mouse press events
        super().mousePressEvent(event)
            
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
        """Paint the planet map."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if self.map_pixmap:
            # Calculate scaled size based on zoom factor
            base_width = self.width()
            base_height = self.height()
            scaled_width = int(base_width * self.zoom_factor)
            scaled_height = int(base_height * self.zoom_factor)
            
            # Draw the map pixmap with zoom and pan
            scaled_pixmap = self.map_pixmap.scaled(
                scaled_width,
                scaled_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Calculate center position with pan offset
            x = (self.width() - scaled_pixmap.width()) // 2 + self.pan_offset_x
            y = (self.height() - scaled_pixmap.height()) // 2 + self.pan_offset_y
            painter.drawPixmap(x, y, scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle resize events to scale the map appropriately."""
        super().resizeEvent(event)
        self.update()
