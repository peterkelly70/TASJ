import logging
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, 
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QGroupBox, QScrollArea, QFrame, QComboBox, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

# Import TravellerMapAPI directly to avoid circular imports
from model.traveller_map_api import TravellerMapAPI

logger = logging.getLogger(__name__)

class SectorMapWidget(QWidget):
    """Widget for displaying the sector map using the Traveller Map API."""
    
    system_selected = pyqtSignal(dict)
    map_error = pyqtSignal(str)  # New signal for map loading errors
    
    # Add destructor to clean up threads
    def __del__(self):
        if hasattr(self, 'loader_thread') and self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()
            
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
        
        # Import the TravellerMapAPI class
        from view.traveller_map_api import TravellerMapAPI
        self.api = TravellerMapAPI
        
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
            
        self.sector_name = sector.get("name")
        self.loading_error = False
        self.error_message = ""
        self.map_pixmap = None
        
        # Update current milieu if provided
        if milieu:
            self.current_milieu = milieu
        
        if self.sector_name:
            # Load map asynchronously
            from PyQt6.QtCore import QThread, pyqtSignal
            
            class MapLoaderThread(QThread):
                map_loaded = pyqtSignal(QPixmap)
                load_failed = pyqtSignal(str)  # Updated to include error message
                
                def __init__(self, api, sector_name, milieu=None):
                    super().__init__()
                    self.api = api
                    self.sector_name = sector_name
                    self.milieu = milieu
                    
                def run(self):
                    try:
                        # Create API instance
                        api_instance = self.api()
                        
                        # Get the sector map from the API with milieu parameter and enhanced options
                        options = {
                            "style": "poster",
                            "scale": 64,
                            "options": "grid,border,routes,names,worlds"
                        }
                        pixmap, error_msg = api_instance.get_sector_map(self.sector_name, self.milieu, options)
                        
                        if pixmap:
                            self.map_loaded.emit(pixmap)
                        else:
                            # Pass the error message along
                            self.load_failed.emit(error_msg or "Unknown error loading sector map")
                    except Exception as e:
                        logger.error(f"Error loading sector map: {e}")
                        self.load_failed.emit(str(e))
            
            # Clean up any existing thread
            if hasattr(self, 'loader_thread') and self.loader_thread and self.loader_thread.isRunning():
                self.loader_thread.quit()
                self.loader_thread.wait()
            
            # Create and start the loader thread
            self.loader_thread = MapLoaderThread(self.api, self.sector_name, self.current_milieu)
            self.loader_thread.map_loaded.connect(self._on_map_loaded)
            self.loader_thread.load_failed.connect(self._on_load_failed)
            self.loader_thread.start()
            
        self.update()
        
    def _on_map_loaded(self, pixmap):
        """Handle successful map loading."""
        self.map_pixmap = pixmap
        self.loading_error = False
        self.error_message = ""
        self.update()
        
    def _on_load_failed(self, error_msg):
        """Handle failed map loading."""
        self.loading_error = True
        self.error_message = error_msg
        self.update()
        # Emit the error signal so parent widgets can display a message
        self.map_error.emit(error_msg)
        
    def paintEvent(self, event):
        """Paint the sector map."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if self.loading_error:
            # Display detailed error message
            painter.setPen(QPen(QColor(255, 100, 100)))
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            
            error_text = f"Error loading map for {self.sector_name}:\n{self.error_message}"
            text_rect = self.rect().adjusted(20, 20, -20, -20)  # Add some padding
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, error_text)
            return
            
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
            
            # Draw system highlights if needed
            if self.selected_system:
                self._highlight_selected_system(painter, scaled_pixmap, x, y)
                
        elif self.loading_error:
            # Show error message
            painter.setPen(QColor(255, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                            f"Error loading map for sector: {self.sector_name}")
        else:
            # Show loading message
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                            "Loading sector map...")
    
    def _highlight_selected_system(self, painter, pixmap, offset_x, offset_y):
        """Highlight the selected system on the map."""
        if not self.selected_system:
            return
            
        # Get hex coordinates
        hex_code = self.selected_system.get('hex_code')
        if not hex_code:
            return
            
        # Draw a highlight for the selected system
        # Since the exact mapping from hex coordinates to pixel positions on the API-provided map
        # would require additional calculations based on the map's scale and origin,
        # we'll display the system name and hex code at the top of the map for now
        painter.setPen(QPen(QColor(255, 255, 0), 2))
        painter.drawText(10, 20, f"Selected: {self.selected_system.get('name', 'Unknown')} ({hex_code})")
        
        # In a future enhancement, we could parse the hex code (e.g., "1010" -> x=10, y=10)
        # and calculate the pixel position based on the map's scale and origin
    
    def mousePressEvent(self, event):
        """Handle mouse press events to select systems."""
        # This would require mapping pixel coordinates to hex coordinates
        # For now, we'll keep the system selection in the systems list
        # and not directly on the map
        pass

class SectorView(QWidget):
    """View for displaying sector and system information."""
    
    # Signals
    system_selected = pyqtSignal(dict)
    planet_selected = pyqtSignal(dict)
    search_requested = pyqtSignal(str)
    milieu_changed = pyqtSignal(str)
    sector_changed = pyqtSignal(dict)  # Signal when a sector is selected
    
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.setWindowTitle("Sector View")
        self.current_sector = None
        self.systems = []
        self.sectors = []
        self.db_path = db_path
        self.current_milieu = "M1105"  # Default milieu
        
        # Initialize database connection
        if self.db_path:
            from model.traveller_database import TravellerDatabase
            self.db_instance = TravellerDatabase(self.db_path)
        else:
            self.db_instance = None
            
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Use full available space
        
        # Sector header with milieu selector
        header_layout = QHBoxLayout()
        self.sector_header = QLabel("Select a Sector")
        self.sector_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.sector_header)
        
        # Add milieu selector to header for better space usage
        milieu_label = QLabel("Milieu:")
        self.milieu_selector = QComboBox()
        self._populate_milieu_selector()
        self.milieu_selector.currentTextChanged.connect(self._on_milieu_changed)
        header_layout.addStretch()
        header_layout.addWidget(milieu_label)
        header_layout.addWidget(self.milieu_selector)
        
        main_layout.addLayout(header_layout)
        
        # Create a splitter for the main content - use a 3-panel layout for better space usage
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent panels from being collapsed
        main_layout.addWidget(splitter, 1)  # Give the splitter a stretch factor
        
        # Left panel - Sectors and systems lists
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins for more space
        
        # Create a vertical splitter for sectors and systems lists
        lists_splitter = QSplitter(Qt.Orientation.Vertical)
        lists_splitter.setChildrenCollapsible(False)  # Prevent panels from being collapsed
        
        # Sectors group
        sectors_widget = QWidget()
        sectors_layout = QVBoxLayout(sectors_widget)
        sectors_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        
        # Sector search bar
        sector_search_layout = QHBoxLayout()
        sector_search_layout.addWidget(QLabel("Search Sectors:"))
        self.sector_search_input = QLineEdit()
        self.sector_search_input.setPlaceholderText("Filter sectors as you type...")
        self.sector_search_input.textChanged.connect(self._on_sector_search_changed)
        sector_search_layout.addWidget(self.sector_search_input)
        sectors_layout.addLayout(sector_search_layout)
        
        # Sectors list
        sectors_group = QGroupBox("Sectors")
        sectors_inner_layout = QVBoxLayout(sectors_group)
        self.sectors_list = QListWidget()
        self.sectors_list.setMinimumHeight(200)  # Ensure minimum height
        self.sectors_list.itemClicked.connect(self._on_sector_selected)
        sectors_inner_layout.addWidget(self.sectors_list)
        sectors_layout.addWidget(sectors_group, 1)  # Give it a stretch factor
        
        lists_splitter.addWidget(sectors_widget)
        
        # Systems group
        systems_widget = QWidget()
        systems_layout = QVBoxLayout(systems_widget)
        systems_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        
        # System search bar and filter options
        system_search_layout = QHBoxLayout()
        system_search_layout.addWidget(QLabel("Search Systems:"))
        self.system_search_input = QLineEdit()
        self.system_search_input.setPlaceholderText("Filter systems as you type...")
        self.system_search_input.textChanged.connect(self._on_system_search_changed)
        system_search_layout.addWidget(self.system_search_input)
        systems_layout.addLayout(system_search_layout)
        
        # Add checkbox to filter out unnamed systems
        filter_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QCheckBox
        self.hide_unnamed_checkbox = QCheckBox("Hide unnamed systems")
        self.hide_unnamed_checkbox.setChecked(False)  # Unchecked by default
        self.hide_unnamed_checkbox.stateChanged.connect(self._on_system_filter_changed)
        filter_layout.addWidget(self.hide_unnamed_checkbox)
        filter_layout.addStretch(1)  # Add stretch to push checkbox to the left
        systems_layout.addLayout(filter_layout)
        
        # Systems list
        systems_group = QGroupBox("Systems in Sector")
        systems_inner_layout = QVBoxLayout(systems_group)
        self.systems_list = QListWidget()
        self.systems_list.itemClicked.connect(self._on_system_selected)
        systems_inner_layout.addWidget(self.systems_list)
        systems_layout.addWidget(systems_group, 1)  # Give it a stretch factor
        
        lists_splitter.addWidget(systems_widget)
        
        # Set initial sizes for the lists splitter (60% sectors, 40% systems)
        lists_splitter.setSizes([600, 400])
        left_layout.addWidget(lists_splitter, 1)  # Give the lists splitter a stretch factor
        
        left_panel.setLayout(left_layout)
        left_panel.setMinimumWidth(250)  # Ensure minimum width
        splitter.addWidget(left_panel)
        
        # Right panel - Map and Info Tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins for more space
        
        # Create a vertical splitter for map and info areas
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setChildrenCollapsible(False)  # Prevent panels from being collapsed
        
        # Middle panel - Map and system details - make it larger
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        
        # Map widget - expanded to use more space
        self.map_widget = SectorMapWidget()
        self.map_widget.setMinimumSize(800, 600)  # Larger minimum size
        self.map_widget.system_selected.connect(self._on_map_system_selected)
        self.map_widget.map_error.connect(self._on_map_error)
        middle_layout.addWidget(self.map_widget, 3)  # Give the map even more space
        
        # Add middle panel to splitter
        right_splitter.addWidget(middle_panel)
        
        # Info area (bottom) will be added in the MapTabsWidget redesign
        
        # Set initial sizes for the right splitter (70% map, 30% info)
        right_splitter.setSizes([700, 300])
        right_layout.addWidget(right_splitter, 1)  # Give the right splitter a stretch factor
        
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(400)  # Ensure minimum width
        splitter.addWidget(right_panel)
        
        # Set the default splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])
        
        self.setLayout(main_layout)
    
    def set_sectors(self, sectors: List[Dict[str, Any]]):
        """Set the available sectors."""
        self.sectors = sorted(sectors, key=lambda s: s.get("name", "").lower())
        self._update_sectors_list()
    
    def set_sector(self, sector: Dict[str, Any]):
        """Set the current sector and update the UI."""
        self.current_sector = sector
        
        # Update header
        name = sector.get("name", "Unknown Sector")
        self.sector_header.setText(f"Sector: {name}")
        
        # Find and select the sector in the dropdown
        for i in range(self.sectors_list.count()):
            sector_data = self.sectors_list.item(i).data(Qt.ItemDataRole.UserRole)
            if sector_data.get("id") == sector.get("id"):
                self.sectors_list.setCurrentItem(self.sectors_list.item(i))
                break
                
        # Update the sector map with the new sector
        self.map_tabs.set_sector(sector)
    
    def set_systems(self, systems: List[Dict[str, Any]]):
        """Set the systems for the current sector."""
        self.systems = systems
        self._update_systems_list()
        # Pass systems to the map tabs widget
        self.map_tabs.set_sector(self.current_sector, systems, self.current_milieu)
    
    def _update_sectors_list(self, search_text=""):
        """Update the sectors list with filtering."""
        self.sectors_list.clear()
        
        # Filter sectors by search text
        filtered_sectors = self.sectors
        if search_text:
            search_text = search_text.lower()
            filtered_sectors = [s for s in self.sectors if search_text in s.get("name", "").lower()]
            
        # Add sectors to list
        for sector in filtered_sectors:
            name = sector.get("name", "Unknown Sector")
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, sector)
            self.sectors_list.addItem(item)
            
    def _update_systems_list(self, systems=None, search_text=""):
        """Update the systems list with the given systems and filtering.
        
        Args:
            systems: List of system dictionaries to display. If None, uses self.systems.
            search_text: Optional text to filter systems by name (case-insensitive).
        """
        if systems is None:
            systems = self.systems
            
        self.systems_list.clear()
        
        filtered_systems = []
        for system in systems:
            # Skip invalid or empty systems
            if not system or not isinstance(system, dict):
                continue
                
            # Get system details
            name = system.get("name", "")
            hex_code = system.get("hex", "")  # Changed from "hex_code" to match DB schema
            uwp = system.get("UWP", "")
            trade_codes = system.get("trade_codes", [])
            
            # Skip empty or invalid systems
            if not name or not hex_code:
                continue
                
            # Skip systems that are completely numeric or empty
            if not name or name.strip() == "" or name.strip().isdigit():
                continue
                
            # Apply search filter if provided
            if search_text and search_text.lower() not in name.lower():
                continue
                
            # Filter out unnamed systems if checkbox is checked
            if hasattr(self, 'hide_unnamed_checkbox') and self.hide_unnamed_checkbox.isChecked():
                if not name or name.startswith("Unnamed") or name.startswith("X"):
                    continue
            
            filtered_systems.append(system)
        
        # Sort systems by hex code (sector position)
        filtered_systems.sort(key=lambda s: s.get("hex", ""))
        
        # Add filtered and sorted systems to the list
        for system in filtered_systems:
            name = system.get("name", "Unknown System")
            hex_code = system.get("hex", "")  # Changed from "hex_code" to match DB schema
            uwp = system.get("UWP", "").strip()
            trade_codes = ", ".join(system.get("trade_codes", []))
            
            # Create a more informative display text
            item_text = f"{hex_code} - {name}"
            if uwp:
                item_text += f" [{uwp}]"
            if trade_codes:
                item_text += f" ({trade_codes})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, system)
            self.systems_list.addItem(item)
    
    def _on_system_selected(self, item, system_data=None):
        """Handle system selection from the list or direct system data.
        
        Args:
            item: The QListWidgetItem that was selected, or None if system_data is provided
            system_data: Optional direct system data dictionary
        """
        logger.info("=== SYSTEM SELECTION STARTED ===")
        logger.debug(f"_on_system_selected called with item={item}, system_data={system_data is not None}")
        
        # Log the full system data if available
        if system_data:
            logger.debug(f"System data received: {system_data}")
        elif item:
            item_data = item.data(Qt.ItemDataRole.UserRole) if item else None
            logger.debug(f"Item data: {item_data}")
            if item_data:
                logger.debug(f"Item data details - Name: {item_data.get('name', 'N/A')}, ID: {item_data.get('id', 'N/A')}")
        
        # Get system data from either direct input or item
        system = None
        if system_data:
            # Direct system data provided
            system = system_data
            logger.info(f"Using direct system data: {system.get('name', 'Unknown')} (ID: {system.get('id', 'N/A')})")
        elif item:
            # Item selected from list
            system = item.data(Qt.ItemDataRole.UserRole)
            if system:
                logger.info(f"Selected system from list: {system.get('name', 'Unknown')} (ID: {system.get('id', 'N/A')})")
            else:
                logger.warning("No system data found in selected item")
        
        # Validate we have a system to work with
        if not system:
            logger.warning("No valid system data available for selection")
            return
            
        # Log system details
        system_name = system.get('name', 'Unknown')
        system_hex = system.get('hex', 'N/A')
        system_id = system.get('id', 'N/A')
        logger.info(f"Processing system selection - Name: {system_name}, Hex: {system_hex}, ID: {system_id}")
        logger.debug(f"Full system data: {system}")
            
        # Emit the system_selected signal to notify other components
        logger.info(f"Emitting system_selected signal for system: {system_name}")
        try:
            self.system_selected.emit(system)
            logger.debug("system_selected signal emitted successfully")
        except Exception as e:
            logger.error(f"Failed to emit system_selected signal: {str(e)}", exc_info=True)
            
        try:
            # Log the current state of map_tabs and sector_map_widget
            map_tabs_exists = hasattr(self, 'map_tabs')
            sector_map_widget_exists = map_tabs_exists and hasattr(self.map_tabs, 'sector_map_widget')
            sector_map_widget = getattr(self.map_tabs, 'sector_map_widget', None) if map_tabs_exists else None
            
            logger.debug(f"map_tabs exists: {map_tabs_exists}")
            logger.debug(f"sector_map_widget exists: {sector_map_widget_exists}")
            logger.debug(f"sector_map_widget type: {type(sector_map_widget) if sector_map_widget else 'None'}")
            
            # Update the map to center on the selected system if available
            if sector_map_widget_exists and sector_map_widget:
                logger.debug("Setting selected system on sector map widget")
                try:
                    sector_map_widget.selected_system = system
                    logger.debug("Successfully set selected_system on sector_map_widget")
                    
                    # Ensure the system has a hex code before trying to center
                    if 'hex' in system and system['hex']:
                        logger.debug(f"Centering on system at hex {system['hex']}")
                        if hasattr(sector_map_widget, 'center_on_system'):
                            sector_map_widget.center_on_system(system)
                            sector_map_widget.update()
                            logger.debug("Successfully centered on system")
                        else:
                            logger.warning("sector_map_widget has no center_on_system method")
                    else:
                        logger.warning(f"System {system_name} is missing hex code")
                    
                    # Also update the info tab if available
                    if hasattr(self.map_tabs, 'update_system_info'):
                        logger.debug("Updating system info via map_tabs.update_system_info")
                        self.map_tabs.update_system_info(system)
                    else:
                        logger.warning("map_tabs has no update_system_info method")
                except Exception as e:
                    logger.error(f"Error updating sector map widget: {str(e)}", exc_info=True)
            else:
                logger.warning("map_tabs or sector_map_widget not available or invalid")
            
            # Update the system info tab directly if available
            if hasattr(self, 'system_info_tab'):
                logger.debug("Updating system info tab directly")
                self._update_system_info_tab(system)
            else:
                logger.debug("system_info_tab not available")
                
        except Exception as e:
            logger.error(f"Unexpected error in system selection handler: {str(e)}", exc_info=True)
            
        # Log completion of system selection
        logger.info(f"=== SYSTEM SELECTION COMPLETED FOR {system_name} ===")
    
    def _on_map_system_selected(self, system):
        """Handle system selection from the map.
        
        Args:
            system: Dictionary containing system data
        """
        logger.debug(f"_on_map_system_selected called with system: {system.get('name', 'Unknown') if system else 'None'}")
        
        if not system:
            logger.debug("No system provided to _on_map_system_selected")
            return
            
        system_name = system.get('name', 'Unknown')
        system_hex = system.get('hex', 'N/A')
        system_id = system.get('id', 'N/A')
        
        logger.info(f"Processing map system selection - Name: {system_name}, Hex: {system_hex}, ID: {system_id}")
            
        # Update the map to center on the selected system
        if hasattr(self, 'map_tabs') and hasattr(self.map_tabs, 'sector_map_widget'):
            logger.debug("Setting selected system on sector map widget from map selection")
            self.map_tabs.sector_map_widget.selected_system = system
            
            # Ensure the system has a hex code before trying to center
            if 'hex' in system and system['hex']:
                logger.debug(f"Centering on system at hex {system['hex']}")
                self.map_tabs.sector_map_widget.center_on_system(system)
                self.map_tabs.sector_map_widget.update()
            else:
                logger.warning(f"System {system_name} is missing hex code")
            
            # Also update the info tab
            logger.debug("Updating system info tab from map selection")
            self.map_tabs.update_system_info(system)
        else:
            logger.warning("map_tabs or sector_map_widget not available in _on_map_system_selected")
        
        # Also select in the list
        logger.debug(f"Searching for system ID {system_id} in systems list")
        system_found = False
        for i in range(self.systems_list.count()):
            item = self.systems_list.item(i)
            if item:
                item_data = item.data(Qt.ItemDataRole.UserRole)
                if item_data and item_data.get("id") == system_id:
                    logger.debug(f"Found matching system in list at index {i}")
                    self.systems_list.setCurrentItem(item)
                    system_found = True
                    break
                    
        if not system_found:
            logger.warning(f"System {system_name} (ID: {system_id}) not found in systems list")
                
        # Emit the signal
        logger.debug(f"Emitting system_selected signal for system from map: {system_name}")
        self.system_selected.emit(system)
        logger.debug("system_selected signal emitted from map selection")
    
    def _on_sector_selected(self, item):
        """Handle sector selection from the list."""
        sector = item.data(Qt.ItemDataRole.UserRole)
        if sector:
            self.current_sector = sector
            name = sector.get("name", "Unknown Sector")
            self.sector_header.setText(f"Sector: {name} (Loading...)")
            
            # Update map tabs with sector data
            self.map_tabs.set_sector(sector, self.current_milieu)
            
            # Load systems for this sector
            self._load_systems_for_sector(sector)
            
            # Update header after loading is complete
            self.sector_header.setText(f"Sector: {name}")
            
            # Clear system search
            self.system_search_input.clear()
            
            # Emit signal
            self.sector_changed.emit(sector)
        else:
            self.sector_header.setText("Select a Sector")
            self.systems_list.clear()
            self.map_tabs.clear_sector()
        
    def _load_systems_for_sector(self, sector):
        """Load systems for the given sector."""
        # In a real app, this would query the database
        # For now, we'll just simulate it
        from model.sectors_db import SectorDB
        import os
        
        # Get database path from environment variable if not provided
        if not self.db_path:
            from dotenv import load_dotenv
            load_dotenv("config/.env")
            self.db_path = os.getenv('DATABASE_FILE_PATH', './database/traveller_campaign.db')
            
        # Create SectorDB instance with proper database instance, not path
        from model.traveller_database import TravellerDatabase
        
        # Ensure we have a proper database instance
        if not hasattr(self, 'db_instance') or self.db_instance is None:
            if self.db_path:
                self.db_instance = TravellerDatabase(self.db_path)
            else:
                # Get database path from environment variable if not provided
                import os
                from dotenv import load_dotenv
                load_dotenv("config/.env")
                db_path = os.getenv('DATABASE_FILE_PATH', './database/traveller_campaign.db')
                self.db_instance = TravellerDatabase(db_path)
                
        # Create SectorDB with proper DB instance
        sector_db = SectorDB(self.db_instance)
        
        # Get systems for this sector
        # The sector ID might be stored as 'sector_id' instead of 'id'
        sector_id = sector.get("sector_id") or sector.get("id")
        
        if sector_id:
            try:
                # Show loading indicator for systems
                self.systems_list.clear()
                self.systems_list.addItem("Loading systems...")
                
                # Use the correct method name: get_systems_for_sector instead of get_systems_by_sector_id
                raw_systems = sector_db.get_systems_for_sector(sector_id)
                
                # Convert tuple records to dictionaries
                systems = []
                if raw_systems:
                    # Get column names from database
                    columns = self.db_instance.get_table_columns("systems")
                    
                    # Convert each tuple to a dictionary
                    for system_tuple in raw_systems:
                        system_dict = {}
                        for i, col in enumerate(columns):
                            if i < len(system_tuple):
                                system_dict[col] = system_tuple[i]
                        systems.append(system_dict)
                
                logger.info(f"Loaded {len(systems) if systems else 0} systems for sector ID {sector_id}")
                self.set_systems(systems)
            except Exception as e:
                logger.error(f"Error loading systems for sector ID {sector_id}: {e}")
                self.set_systems([])
        else:
            logger.error(f"No sector ID found in sector data: {sector}")
            self.set_systems([])
        
    def _on_sector_search_changed(self, text):
        """Filter the sectors list as the user types."""
        self._update_sectors_list(text)
            
    def _on_system_search_changed(self, text):
        """Handle system search text changes."""
        self._update_systems_list(search_text=text)
        
    def _on_system_filter_changed(self, state):
        """Handle system filter checkbox state changes."""
        # Update the systems list with current search text and filter settings
        self._update_systems_list(search_text=self.system_search_input.text())
        
    def _populate_milieu_selector(self):
        """Populate the milieu selector with available milieux from the TravellerMap API."""
        # Get available milieux from settings or use defaults
        from controller.settings_controller import SettingsController
        self.settings = SettingsController()
        
        # Get current milieu preference
        self.current_milieu = self.settings.load_milieu()
        
        # Show loading indicator
        self.milieu_selector.clear()
        self.milieu_selector.addItem("Loading milieux...")
        self.milieu_selector.setEnabled(False)
        
        # Use a thread to fetch milieux from the API
        from PyQt6.QtCore import QThread, pyqtSignal
        from model.traveller_map_api import TravellerMapAPI
        
        class MilieuLoaderThread(QThread):
            milieux_loaded = pyqtSignal(list)
            load_failed = pyqtSignal(str)
            
            def run(self):
                try:
                    api = TravellerMapAPI()
                    milieux_data = api.get_available_milieux()
                    self.milieux_loaded.emit(milieux_data)
                except Exception as e:
                    self.load_failed.emit(str(e))
        
        # Create and start the thread
        self.milieu_loader = MilieuLoaderThread()
        self.milieu_loader.milieux_loaded.connect(self._on_milieux_loaded)
        self.milieu_loader.load_failed.connect(self._on_milieux_load_failed)
        self.milieu_loader.start()
        
    def _on_milieux_loaded(self, milieux_data):
        """Handle successful loading of milieux from API."""
        self.milieu_selector.clear()
        self.milieu_selector.setEnabled(True)
        
        # Define descriptive names for milieux
        milieu_descriptions = {
            "IW": "The Interstellar Wars",
            "M0": "Early Imperium (Milieu 0)",
            "M600": "Milieu 600",
            "M990": "Solomani Rim War (990)",
            "M1105": "The Golden Age (1105, default)",
            "M1120": "The Rebellion (1120)",
            "M1201": "The New Era (1201)",
            "M1248": "The New, New Era (1248)",
            "M1900": "The Far Far Future (1900)"
        }
        
        # Store code to description mapping for later use
        self.milieu_codes = {}
        
        # Process milieux data
        default_milieu = None
        for milieu in milieux_data:
            code = milieu.get("Code", "")
            if code:
                # Get descriptive name or use code if not found
                description = milieu_descriptions.get(code, code)
                
                # Store the mapping
                self.milieu_codes[description] = code
                
                # Add to selector with descriptive name
                self.milieu_selector.addItem(description)
                
                if milieu.get("IsDefault", False):
                    default_milieu = description
        
        # If no milieux were loaded, add default ones
        if self.milieu_selector.count() == 0:
            default_milieux = ["M1105", "M1248", "M990", "M0", "M1900", "IW", "M600", "M1120", "M1201"]
            for milieu in default_milieux:
                self.milieu_selector.addItem(milieu)
        
        # Set current milieu from settings or use default
        index = self.milieu_selector.findText(self.current_milieu)
        if index >= 0:
            self.milieu_selector.setCurrentIndex(index)
        elif default_milieu:
            index = self.milieu_selector.findText(default_milieu)
            if index >= 0:
                self.milieu_selector.setCurrentIndex(index)
                
    def _on_milieux_load_failed(self, error_msg):
        """Handle failed loading of milieux from API."""
        self.milieu_selector.clear()
        self.milieu_selector.setEnabled(True)
        
        # Define descriptive names for milieux
        milieu_descriptions = {
            "IW": "The Interstellar Wars",
            "M0": "Early Imperium (Milieu 0)",
            "M600": "Milieu 600",
            "M990": "Solomani Rim War (990)",
            "M1105": "The Golden Age (1105, default)",
            "M1120": "The Rebellion (1120)",
            "M1201": "The New Era (1201)",
            "M1248": "The New, New Era (1248)",
            "M1900": "The Far Far Future (1900)"
        }
        
        # Store code to description mapping for later use
        self.milieu_codes = {}
        
        # Add default milieux as fallback with descriptive names
        default_milieux = ["M1105", "M1248", "M990", "M0", "M1900", "IW", "M600", "M1120", "M1201"]
        for code in default_milieux:
            # Get descriptive name or use code if not found
            description = milieu_descriptions.get(code, code)
            
            # Store the mapping
            self.milieu_codes[description] = code
            
            # Add to selector with descriptive name
            self.milieu_selector.addItem(description)
        
        # Find the current milieu's descriptive name
        current_description = None
        for desc, code in self.milieu_codes.items():
            if code == self.current_milieu:
                current_description = desc
                break
        
        # Set current milieu
        if current_description:
            index = self.milieu_selector.findText(current_description)
            if index >= 0:
                self.milieu_selector.setCurrentIndex(index)
        else:
            # Fallback to finding by code
            index = self.milieu_selector.findText(self.current_milieu)
            if index >= 0:
                self.milieu_selector.setCurrentIndex(index)
    
    def _on_milieu_changed(self, milieu_description):
        """Handle milieu selection change."""
        # Convert descriptive name to code
        # Ensure milieu_codes exists to prevent AttributeError
        if not hasattr(self, 'milieu_codes'):
            self.milieu_codes = {}
            
        milieu_code = self.milieu_codes.get(milieu_description, milieu_description)
        
        if milieu_code != self.current_milieu:
            # Update current milieu
            self.current_milieu = milieu_code
            
            # Save preference
            self.settings.save_milieu(milieu_code)
            
            # Emit signal for other components
            self.milieu_changed.emit(milieu_code)
            
            # Reload sectors list with the new milieu
            self._reload_sectors_for_milieu(milieu_code)
            
            # Update current sector if one is selected
            if self.current_sector:
                self.map_tabs.set_sector(self.current_sector, milieu_code)
                self._load_systems_for_sector(self.current_sector)
                
    def _update_system_info_tab(self, system):
        """Update the system info tab with the selected system's data.
        
        Args:
            system: Dictionary containing system data
        """
        try:
            if not system:
                logger.warning("No system data provided to update system info tab")
                return
                
            logger.debug(f"Updating system info tab for system: {system.get('name', 'Unknown')}")
            
            # Get or create the system info tab
            if not hasattr(self, 'system_info_tab'):
                self.system_info_tab = QWidget()
                layout = QVBoxLayout(self.system_info_tab)
                
                # Create a scroll area for the system info
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                
                # Create a widget to contain the system info
                self.system_info_widget = QWidget()
                self.system_info_layout = QVBoxLayout(self.system_info_widget)
                
                # Add the system info widget to the scroll area
                scroll.setWidget(self.system_info_widget)
                
                # Add the scroll area to the tab's layout
                layout.addWidget(scroll)
                
                # Add the tab if it doesn't exist
                if hasattr(self, 'info_tabs') and isinstance(self.info_tabs, QTabWidget):
                    self.info_tabs.addTab(self.system_info_tab, "System Info")
            
            # Clear previous content
            while self.system_info_layout.count():
                item = self.system_info_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add system information
            system_name = system.get('name', 'Unknown System')
            name_label = QLabel(f"<h2>{system_name}</h2>")
            self.system_info_layout.addWidget(name_label)
            
            # Basic system info
            info_text = f"<b>Hex:</b> {system.get('hex', 'N/A')}<br>"
            info_text += f"<b>UWP:</b> {system.get('UWP', 'N/A')}<br>"
            info_text += f"<b>Trade Codes:</b> {', '.join(system.get('trade_codes', [])) or 'None'}<br>"
            info_text += f"<b>Travel Zone:</b> {system.get('zone', 'None')}<br>"
            info_text += f"<b>PBG:</b> {system.get('pbg', 'N/A')}<br>"
            info_text += f"<b>Allegiance:</b> {system.get('allegiance', 'N/A')}<br>"
            info_text += f"<b>Stars:</b> {system.get('stars', 'N/A')}<br>"
            
            # Add planets if available
            if 'planets' in system and system['planets']:
                info_text += "<br><b>Planets:</b><br>"
                for planet in system['planets']:
                    info_text += f"- {planet.get('name', 'Unnamed Planet')}: "
                    info_text += f"{planet.get('uwp', 'N/A')} {planet.get('trade_codes', [])}<br>"
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            self.system_info_layout.addWidget(info_label)
            
            # Add stretch to push content to the top
            self.system_info_layout.addStretch()
            
            # Switch to the system info tab
            if hasattr(self, 'info_tabs') and isinstance(self.info_tabs, QTabWidget):
                self.info_tabs.setCurrentWidget(self.system_info_tab)
                
        except Exception as e:
            logger.error(f"Error updating system info tab: {str(e)}", exc_info=True)
            
    def _reload_sectors_for_milieu(self, milieu):
        """Reload sectors list for the selected milieu."""
        try:
            # Get sectors from the database filtered by milieu
            from controller.sectors_controller import SectorController
            
            # Use the already initialized database instance
            if not hasattr(self, 'db_instance') or not self.db_instance:
                from model.traveller_database import TravellerDatabase
                self.db_instance = TravellerDatabase(self.db_path)
                
            sectors_controller = SectorController(self.db_instance)
            sectors = sectors_controller.get_sectors_by_milieu(milieu)
            
            # Convert DB records to dictionaries
            sector_dicts = []
            for sector in sectors:
                sector_id, name, x, y, desc, img_path, abbrev, milieu = sector
                sector_dicts.append({
                    "sector_id": sector_id,
                    "name": name or f"Unnamed Sector {sector_id}",
                    "x_coordinate": x,
                    "y_coordinate": y,
                    "description": desc,
                    "image_path": img_path,
                    "abbreviation": abbrev,
                    "milieu": milieu
                })
            
            # Update sectors list
            self.set_sectors(sector_dicts)
            
            # Clear current sector if it's not in the new milieu
            if self.current_sector:
                found = False
                for sector in sector_dicts:
                    if sector["sector_id"] == self.current_sector.get("sector_id"):
                        found = True
                        break
                if not found:
                    self.current_sector = None
                    self.sector_header.setText("Select a Sector")
                    self.systems_list.clear()
        except Exception as e:
            logger.error(f"Error loading sectors for milieu {milieu}: {e}")
            self.sectors_list.clear()
            self.sectors_list.addItem(f"Error: {str(e)}")
    
    def set_db_path(self, db_path):
        """Set the database path."""
        self.db_path = db_path
        self.map_tabs.set_db_path(db_path)
            
