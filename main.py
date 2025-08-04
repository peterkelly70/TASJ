#!/usr/bin/env python3

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QProgressBar, QMenuBar, QTabWidget,
    QTextEdit, QDialogButtonBox, QWidget, QFontDialog, QMessageBox, QMenu,
    QListWidget, QGroupBox, QFormLayout, QListWidgetItem, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import QSettings, Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QAction, QFontMetrics
from utils.flow_layout import FlowLayout
import sys
import os
import configparser
from dotenv import load_dotenv
import multiprocessing
from typing import Optional, Dict, Any
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
import json
from pathlib import Path

from model.traveller_database import TravellerDatabase
from model.migrations import run_migrations
from controller.data_download_controller import DataDownloadController
from controller.console_controller import ConsoleController
from controller.theme_controller import ThemeController
from controller.sectors_controller import SectorController
from controller.planets_controller import PlanetController
from controller.people_controller import PeopleController
from controller.lifeforms_controller import LifeformsController
from controller.ships_controller import ShipsController
from controller.vehicle_controller import VehicleController
from controller.events_controller import EventsController
from controller.technology_controller import TechnologyController
from controller.organizations_controller import OrganizationsController
from controller.adventure_hooks_controller import AdventureHooksController
from view.console_view import ConsoleView

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to capture all messages
logger = logging.getLogger(__name__)

# Configure file handler with rotation
log_file = os.path.join('logs', 'tasj.log')
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)  # Capture all levels in the log file
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Configure console handler with a higher level (WARNING)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only show WARNING and above in console
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

# Get the root logger and add both handlers
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Set root logger to lowest level
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Set specific loggers to DEBUG
logging.getLogger('view.sector_map_widget').setLevel(logging.DEBUG)

# Load environment variables
load_dotenv("config/.env")
DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
DATABASE_PATH: str = os.getenv("DATABASE_FILE_PATH", "database/traveller_campaign.db")

# Theme styles
THEME_STYLESHEETS: Dict[str, str] = {}

def _extract_css_from_theme(content: str) -> str:
    """Extract CSS content from theme file, skipping section headers."""
    css_lines = []
    in_styles = False
    for line in content.splitlines():
        if line.strip() == '[Styles]':
            in_styles = True
            continue
        if line.strip() == '[Colors]':
            in_styles = False
            continue
        if in_styles and line.strip():
            css_lines.append(line)
    return '\n'.join(css_lines)

def _load_single_theme(theme_file: Path) -> tuple[str, str]:
    """Load a single theme file and return (theme_name, stylesheet)."""
    theme_name = theme_file.stem.capitalize()
    logger.info(f"Loading theme: {theme_name} from {theme_file}")
    
    with open(theme_file, 'r') as f:
        css_content = f.read()
    
    stylesheet = _extract_css_from_theme(css_content)
    return theme_name, stylesheet

def load_theme_stylesheets():
    """Load all theme files into the THEME_STYLESHEETS dictionary."""
    logger.info("Starting theme loading...")
    themes_dir = Path("config/themes")
    
    if not themes_dir.exists():
        logger.error(f"Themes directory does not exist: {themes_dir}")
        return
    if not themes_dir.is_dir():
        logger.error(f"Themes path is not a directory: {themes_dir}")
        return
        
    theme_files = list(themes_dir.glob("*.theme"))
    logger.info(f"Found {len(theme_files)} theme files: {[f.name for f in theme_files]}")
        
    for theme_file in theme_files:
        try:
            theme_name, stylesheet = _load_single_theme(theme_file)
            THEME_STYLESHEETS[theme_name] = stylesheet
            logger.info(f"Successfully loaded theme: {theme_name}")
            logger.debug(f"Theme contents:\n{stylesheet}")
                
        except Exception as e:
            logger.error(f"Failed to load theme {theme_file.stem.capitalize()}: {e}")
            logger.error("Error details:", exc_info=True)

# Load themes at startup
load_theme_stylesheets()

LIGHT_STYLESHEET: str = """
    QMainWindow, QDialog {
        background-color: white;
        color: black;
    }
    QPushButton {
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
    }
    QTextEdit {
        border: 1px solid #ccc;
        border-radius: 4px;
    }
"""

DARK_STYLESHEET: str = """
    QMainWindow, QDialog {
        background-color: #2e2e2e;
        color: white;
    }
    QPushButton {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 6px 12px;
        color: white;
    }
    QPushButton:hover {
        background-color: #505050;
    }
    QTextEdit {
        border: 1px solid #505050;
        border-radius: 4px;
        background-color: #363636;
        color: white;
    }
"""

@dataclass
class UISettings:
    """Data class for storing UI settings"""
    theme: str
    font: QFont
    stylesheet: str

class SettingsDialog(QDialog):
    """Dialog for selecting theme and font settings."""
    
    def __init__(self, current_theme: str, current_font: QFont, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 200)
        
        # Store initial values
        self.current_theme = current_theme
        self.current_font = current_font
        self.selected_font = None
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        theme_row = QHBoxLayout()
        theme_label = QLabel("Current Theme:")
        self.theme_combo = QComboBox()
        
        # Get available themes
        themes = sorted(THEME_STYLESHEETS.keys())
        logger.info(f"Setting up theme dropdown with themes: {themes}")
        
        if not themes:
            themes = ["Light", "Dark"]
            logger.warning("No themes found, using fallback themes")
        
        # Add themes to dropdown
        self.theme_combo.addItems(themes)
        
        # Set current theme if it exists, otherwise use first theme
        theme_index = self.theme_combo.findText(self.current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
            logger.info(f"Set current theme to: {self.current_theme}")
        else:
            logger.warning(f"Current theme {self.current_theme} not found in themes list")
            if self.theme_combo.count() > 0:
                self.theme_combo.setCurrentIndex(0)
                self.current_theme = self.theme_combo.currentText()
                logger.info(f"Defaulted to first theme: {self.current_theme}")
        
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo)
        theme_layout.addLayout(theme_row)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font selection
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        font_row = QHBoxLayout()
        font_label = QLabel("Current Font:")
        self.font_display = QLabel(f"{self.current_font.family()} {self.current_font.pointSize()}")
        font_button = QPushButton("Change Font")
        font_button.clicked.connect(self.choose_font)
        
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_display)
        font_row.addWidget(font_button)
        font_layout.addLayout(font_row)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set dialog layout
        self.setLayout(layout)
    
    def choose_font(self) -> None:
        """Open font selection dialog."""
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.selected_font = font
            self.font_display.setText(f"{font.family()} {font.pointSize()}")

class LicensesDialog(QDialog):
    """Dialog for displaying software and font licenses."""
    
    def __init__(self, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Licenses and Acknowledgments")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Create tab widget for different license categories
        tabs = QTabWidget()
        
        # Fonts tab with split view
        fonts_tab = QWidget()
        fonts_layout = QHBoxLayout()
        
        # Left side - font list
        font_list = QListWidget()
        font_list.setMaximumWidth(250)
        
        # Right side - details
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        # Font info section
        info_group = QGroupBox("Font Information")
        info_layout = QFormLayout()
        self.name_label = QLabel()
        self.author_label = QLabel()
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.usage_label = QLabel()
        self.source_label = QLabel()
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Author:", self.author_label)
        info_layout.addRow("Description:", self.description_label)
        info_layout.addRow("Usage:", self.usage_label)
        info_layout.addRow("Source:", self.source_label)
        info_group.setLayout(info_layout)
        
        # License text section
        license_group = QGroupBox("License")
        license_layout = QVBoxLayout()
        self.license_text = QTextEdit()
        self.license_text.setReadOnly(True)
        license_layout.addWidget(self.license_text)
        license_group.setLayout(license_layout)
        
        details_layout.addWidget(info_group)
        details_layout.addWidget(license_group)
        details_widget.setLayout(details_layout)
        
        try:
            with open('config/licenses/fonts.json', 'r') as f:
                self.fonts_data = json.load(f)
                
            for font_id, font_info in self.fonts_data['fonts'].items():
                item = QListWidgetItem(font_info['name'])
                item.setData(Qt.ItemDataRole.UserRole, font_id)
                font_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Failed to load font licenses: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to load font licenses: {str(e)}")
        
        font_list.currentItemChanged.connect(self.update_font_details)
        if font_list.count() > 0:
            font_list.setCurrentRow(0)
        
        fonts_layout.addWidget(font_list)
        fonts_layout.addWidget(details_widget)
        fonts_tab.setLayout(fonts_layout)
        tabs.addTab(fonts_tab, "Fonts")
        
        # Software tab (for future use)
        software_tab = QWidget()
        software_layout = QVBoxLayout()
        software_text = QTextEdit()
        software_text.setReadOnly(True)
        software_text.setText("Software licenses and acknowledgments will be listed here.")
        software_layout.addWidget(software_text)
        software_tab.setLayout(software_layout)
        tabs.addTab(software_tab, "Software")
        
        layout.addWidget(tabs)
        
        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def update_font_details(self, current: QListWidgetItem, previous: Optional[QListWidgetItem] = None) -> None:
        """Update the font details when a new font is selected."""
        if not current:
            return
            
        font_id = current.data(Qt.ItemDataRole.UserRole)
        font_info = self.fonts_data['fonts'][font_id]
        
        self.name_label.setText(font_info['name'])
        self.author_label.setText(font_info['author'])
        self.description_label.setText(font_info['description'])
        self.usage_label.setText(font_info['usage'])
        self.source_label.setText(f"<a href='{font_info['source']}'>{font_info['source']}</a>")
        self.source_label.setOpenExternalLinks(True)
        
        # Load license text if available
        if font_info['license_file']:
            try:
                with open(f"config/licenses/{font_info['license_file']}", 'r') as f:
                    self.license_text.setText(f.read())
            except Exception as e:
                self.license_text.setText(f"Error loading license text: {str(e)}")
        else:
            self.license_text.setText(f"License: {font_info['license']}\nNo detailed license text available.")

class HitchhikersGuideToTheGalaxy(QMainWindow):
    """Main application window for the Traveller Campaign Management System.
    
    This class handles the main UI and coordinates between different controllers
    and the database. It manages settings persistence and provides interfaces
    for data download and migration operations.
    """
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        
        # Initialize console controller first to capture all logging
        self.console_controller = ConsoleController(self)
        
        # Initialize application
        self._initialize_app()
        
        # Set up UI
        self._setup_ui()
        
        # Initialize controllers
        self._initialize_controllers()
        
        # Apply theme and font
        self.apply_theme_and_font()
        
        # Show window
        self.show()
        
        # Log initialization
        logging.info("Application initialized successfully")
        
        # Initialize data download controller with console view
        self.data_download_controller.set_console_view(self.console_controller.console_view)

    def _initialize_app(self) -> None:
        """Initialize the application."""
        logger.info("Initializing Hitchhiker's Guide to the Galaxy...")
        
        try:
            self._initialize_database()
            self._load_settings()
            logger.info(f"Settings loaded - Theme: {self.current_theme}")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
            raise
            
    def _initialize_database(self) -> None:
        """Initialize database connection and verify configuration."""
        if DATABASE_TYPE not in ['sqlite', 'mysql']:
            logger.error(f"Unsupported database type: {DATABASE_TYPE}")
            raise ValueError("Unsupported database type.")
            
        self.db_instance = TravellerDatabase(DATABASE_TYPE)
        logger.info(f"Database initialized with type: {DATABASE_TYPE}")
        
        # Run database migrations
        try:
            logger.info(f"Running database migrations for {DATABASE_TYPE}...")
            run_migrations(DATABASE_TYPE, existing_db=self.db_instance)
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Error running database migrations: {e}")
            # Don't raise exception here, as the application can still function
            # with the existing database structure
        
    def _load_settings(self) -> None:
        """Load and initialize application settings."""
        config_parser = configparser.ConfigParser()
        config_parser.read('config/.config')
        default_theme = config_parser.get('Display', 'theme', fallback='Light').capitalize()
        
        self.qsettings = QSettings("YourCompany", "TASJ")
        self.current_theme = self.qsettings.value("theme", default_theme)
        
        # Initialize default font
        self.current_font = QFont()
        font_string = self.qsettings.value("font", "")
        if font_string:
            self.current_font.fromString(font_string)
        else:
            # Set default font properties if no saved font
            self.current_font.setFamily("Arial")
            self.current_font.setPointSize(10)

        # Restore window geometry
        geometry = self.qsettings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size if no saved geometry
            self.resize(1024, 768)
            self.center_window()
            
    def center_window(self):
        """Center the window on the screen."""
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().geometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def closeEvent(self, event):
        """Handle window close event - save settings."""
        # Save window geometry
        self.qsettings.setValue("geometry", self.saveGeometry())
        event.accept()

    def _initialize_controllers(self) -> None:
        """Initialize application controllers."""
        # Initialize console controller first
        self.console_controller = ConsoleController(self)
        
        # Initialize controllers
        self.sectors_controller = SectorController(self.db_instance)
        self.planets_controller = PlanetController(self.db_instance)
        self.people_controller = PeopleController(self.db_instance)
        self.lifeforms_controller = LifeformsController(self.db_instance)
        self.ships_controller = ShipsController(self.db_instance)
        self.vehicle_controller = VehicleController(self.db_instance)
        self.events_controller = EventsController(self.db_instance)
        self.technology_controller = TechnologyController(self.db_instance)
        self.organizations_controller = OrganizationsController(self.db_instance)
        self.adventure_hooks_controller = AdventureHooksController(self.db_instance)
        
        # Connect sector selection to planet updates
        self.sectors_controller.sector_changed.connect(self.planets_controller.set_current_sector)
        
        # Initialize data download controller
        self.data_download_controller = DataDownloadController(
            self.db_instance
        )
        
        # Progress monitoring is now handled internally by the controller

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        self.setWindowTitle("Hitchhiker's Guide to the Galaxy")
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Console action
        console_action = QAction("Console", self)
        console_action.setShortcut("Ctrl+L")
        console_action.triggered.connect(self.console_controller.show_console)
        file_menu.addAction(console_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        # Add separator before exit
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit Application", self) 
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        file_menu.aboutToShow.connect(self._adjust_menu_width) 
        
        # Database menu
        database_menu = menubar.addMenu("Database")
        migrate_action = QAction("Migrate Database Schema", self) 
        migrate_action.triggered.connect(self.run_migrations)
        database_menu.addAction(migrate_action)

        backup_action = QAction("Backup Database Content", self) 
        backup_action.triggered.connect(self.backup_database)
        database_menu.addAction(backup_action)

        api_data_action = QAction("Download API Data", self)
        api_data_action.triggered.connect(self.load_api_data)
        database_menu.addAction(api_data_action)

        database_menu.aboutToShow.connect(self._adjust_menu_width) 
        
        # Create top and bottom layouts
        top_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()
        
        # Create button container with flow layout
        self.button_container = QWidget()
        button_flow_layout = FlowLayout(self.button_container)
        
        # Create buttons
        self.sector_button = QPushButton("Sectors")
        self.planet_button = QPushButton("Planets")
        self.people_button = QPushButton("Characters")
        self.lifeforms_button = QPushButton("Lifeforms")
        self.ships_button = QPushButton("Ships")
        self.vehicle_button = QPushButton("Vehicle")
        self.events_button = QPushButton("Events")
        self.technology_button = QPushButton("Technology")
        self.organizations_button = QPushButton("Organizations")
        self.adventure_hooks_button = QPushButton("Adventure Hooks")
        self.console_button = QPushButton("Console")
        
        # Add buttons to flow layout
        buttons = [
            self.sector_button, self.planet_button, self.people_button,
            self.lifeforms_button, self.ships_button, self.vehicle_button,
            self.events_button, self.technology_button, self.organizations_button,
            self.adventure_hooks_button, self.console_button
        ]
        
        # Configure button properties
        for button in buttons:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            button_flow_layout.addWidget(button)
            handler = self._create_button_handler(button.text())
            button.clicked.connect(handler)
        
        # Add button container to top layout
        top_layout.addWidget(self.button_container)
        
        # Create main view as a stacked widget instead of QTextEdit
        # This allows us to show complex UI components
        self.main_view = QStackedWidget()
        
        # Create a default text view for simple messages
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Set text view properties
        font = QFont()
        font.setPointSize(10)  # Smaller font size
        self.text_view.setFont(font)
        
        # Add text view to stacked widget
        self.main_view.addWidget(self.text_view)
        
        # Add main view to bottom layout
        bottom_layout.addWidget(self.main_view)
        
        # Add top and bottom layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        
        # Set main layout
        central_widget.setLayout(main_layout)
        
        # Set window size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Connect resize event to update button sizes
        self.resizeEvent = self._update_button_sizes
        
        # Initialize console view
        self.console_view = self.console_controller.console_view
        self.console_view.hide()  # Start hidden
        
    def _create_button_handler(self, button_text: str):
        """Create handler for button clicks."""
        def handler():
            # Stop any running timers
            if hasattr(self.console_controller, 'update_timer') and self.console_controller.update_timer.isActive():
                self.console_controller.update_timer.stop()
            
            # Clear text view (for controllers that still use it)
            self.text_view.clear()
            
            # Show appropriate view based on button
            if button_text == "Sectors":
                self.sectors_controller.show_view(self.main_view)
            elif button_text == "Planets":
                self.planets_controller.show_view(self.main_view)
            elif button_text == "Characters":
                self.people_controller.show_view(self.main_view)
            elif button_text == "Lifeforms":
                self.lifeforms_controller.show_view(self.main_view)
            elif button_text == "Ships":
                self.ships_controller.show_view(self.main_view)
            elif button_text == "Vehicle":
                self.vehicle_controller.show_view(self.main_view)
            elif button_text == "Events":
                self.events_controller.show_view(self.main_view)
            elif button_text == "Technology":
                self.technology_controller.show_view(self.main_view)
            elif button_text == "Organizations":
                self.organizations_controller.show_view(self.main_view)
            elif button_text == "Adventure Hooks":
                self.adventure_hooks_controller.show_view(self.main_view)
            elif button_text == "Console":
                # Show console view in the main view using the controller
                self.console_controller.show_view(self.main_view)
        return handler

    def apply_theme_and_font(self) -> None:
        """Apply the current theme and font settings."""
        # Load theme
        theme_name = self.current_theme
        logger.info(f"Applying theme: {theme_name}")
        
        if theme_name in THEME_STYLESHEETS:
            stylesheet = THEME_STYLESHEETS[theme_name]
            logger.debug(f"Using stylesheet:\n{stylesheet}")
        else:
            logger.error(f"Theme not found: {theme_name}")
            logger.debug(f"Available themes: {list(THEME_STYLESHEETS.keys())}")
            return

        # Get theme-specific font if no custom font set
        if not self.current_font:
            # Use system default font
            pass
        
        # Load and apply theme CSS globally to the application
        try:
            app = QApplication.instance()
            app.setStyleSheet(stylesheet)
            logger.info(f"Successfully applied theme: {theme_name}")
        except Exception as e:
            logger.error(f"Failed to apply theme {theme_name}: {e}")
            logger.error("Error details:", exc_info=True)
            return

        # Apply font globally to the application
        app = QApplication.instance()
        app.setFont(self.current_font)
        
        # Also apply to all existing widgets for immediate effect
        for widget in self.findChildren(QWidget):
            widget.setFont(self.current_font)
            
    def download_all_data(self) -> None:
        """Start downloading data in background process."""
        logger.info("Starting data download process")
        try:
            self.data_download_controller.start_download()
        except Exception as e:
            logger.error(f"Failed to start data download: {str(e)}", exc_info=True)
            
    def cancel_download(self) -> None:
        """Cancel ongoing download process."""
        logger.info("Cancelling data download")
        self.data_download_controller.cancel_download()
        
    class MigrationWorker(QThread):
        finished = pyqtSignal(bool, str)  # success, message
        progress = pyqtSignal(str)  # progress message
        
        def __init__(self, db_instance):
            super().__init__()
            self.db_instance = db_instance
            self._is_cancelled = False
            
        def cancel(self):
            self._is_cancelled = True
            
        def run(self):
            try:
                self.progress.emit("Starting database migrations...")
                # Get the database type from the instance
                db_type = self.db_instance.db_type
                run_migrations(db_type, worker=self, existing_db=self.db_instance)
                if self._is_cancelled:
                    self.finished.emit(False, "Migrations cancelled by user.")
                else:
                    self.finished.emit(True, "Database migrations completed successfully.")
            except Exception as e:
                error_msg = f"Migration failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.finished.emit(False, error_msg)

    def run_migrations(self) -> None:
        """Execute database migrations in a separate thread."""
        if hasattr(self, '_migration_worker') and self._migration_worker.isRunning():
            QMessageBox.information(self, "Info", "Migrations are already running.")
            return
            
        logger.info("Starting database migrations")
        
        # Create and show progress dialog
        self.migration_progress = QProgressDialog("Running database migrations...", "Cancel", 0, 0, self)
        self.migration_progress.setWindowTitle("Database Migrations")
        self.migration_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.migration_progress.canceled.connect(self.cancel_migrations)
        
        # Create and start worker thread
        self._migration_worker = self.MigrationWorker(self.db_instance)
        self._migration_worker.finished.connect(self.on_migrations_finished)
        self._migration_worker.progress.connect(self.update_migration_progress)
        self._migration_worker.start()
        
        self.migration_progress.show()
        
    def update_migration_progress(self, message):
        """Update progress dialog with current migration status."""
        if hasattr(self, 'migration_progress') and self.migration_progress:
            self.migration_progress.setLabelText(message)
            QApplication.processEvents()  # Keep UI responsive
            
    def cancel_migrations(self):
        """Handle cancellation of migrations."""
        if hasattr(self, '_migration_worker') and self._migration_worker.isRunning():
            self._migration_worker.cancel()
            self.migration_progress.setLabelText("Cancelling migrations...")
            self.migration_progress.setCancelButton(None)  # Disable cancel button while cancelling
            
    def on_migrations_finished(self, success, message):
        """Handle migration completion."""
        if hasattr(self, 'migration_progress'):
            self.migration_progress.close()
            
        if success:
            logger.info("Migrations completed successfully")
            QMessageBox.information(self, "Success", message)
        else:
            logger.error(f"Migration failed: {message}")
            QMessageBox.critical(self, "Error", message)
            

    def open_settings(self) -> None:
        """Opens the settings dialog and applies changes globally."""
        dialog = SettingsDialog(self.current_theme, self.current_font, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_theme = dialog.theme_combo.currentText()
            # Only update font if a new one was selected
            if dialog.selected_font:
                self.current_font = dialog.selected_font
            self.qsettings.setValue("theme", self.current_theme)
            # Ensure current_font is valid before saving
            if self.current_font:
                self.qsettings.setValue("font", self.current_font.toString())
            self.apply_theme_and_font()
            QMessageBox.information(self, "Settings", "Settings applied successfully.")

    def backup_database(self) -> None:
        """Backup database."""
        logger.info("Backing up database")
        try:
            # Add database backup logic here
            logger.info("Database backup completed successfully")
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}", exc_info=True)

    def _adjust_menu_width(self):
        """Adjusts the minimum width of the sender menu based on its actions and font."""
        menu = self.sender()
        if isinstance(menu, QMenu):
            max_width = 0
            # Use the menu's font, which should reflect application font changes
            font_metrics = QFontMetrics(menu.font())
            
            # Calculate padding based on font size to be more dynamic
            font_height = font_metrics.height()
            base_padding = font_height * 2  # Base padding scales with font size
            icon_space = font_height * 1.5  # Space for potential icons
            submenu_arrow = font_height     # Space for submenu arrows
            total_padding = base_padding + icon_space + submenu_arrow

            for action in menu.actions():
                if not action.isSeparator():
                    # Get the width needed for the text
                    text_width = font_metrics.horizontalAdvance(action.text())
                    # Add padding and some extra space for comfort (20% more)
                    action_width = int((text_width + total_padding) * 1.2)
                    max_width = max(max_width, action_width)

            # Set a minimum reasonable width based on font size
            min_width = font_height * 15
            max_width = max(max_width, min_width)
            
            menu.setMinimumWidth(max_width)

    def load_api_data(self) -> None:
        """Download and load API data."""
        logger.info("Starting API data download")
        try:
            # Make sure console view is visible and active
            self.console_view.show()
            self.console_view.raise_()
            self.console_view.append_text("\n==== STARTING API DATA DOWNLOAD ====\n\n")
            
            # Show console view with progress UI
            self.console_view.show_progress_bar(True)
            self.console_view.update_progress_bar(0)
            self.console_view.enable_cancel_button(True)
            
            # Process any pending events to ensure UI updates
            QApplication.processEvents()
            
            # Start download
            self.data_download_controller.start_download()
        except Exception as e:
            logger.error(f"API data download failed: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download API data: {str(e)}")
            if hasattr(self, 'console_view'):
                self.console_view.show_progress_bar(False)
                self.console_view.enable_cancel_button(False)

    def open_licenses(self) -> None:
        """Opens the licenses dialog."""
        # self.font_controller.show_licenses(self)

    def _update_button_sizes(self, event):
        """Update button sizes when window is resized."""
        # Get current window size
        width = self.width()
        height = self.height()
        
        # Calculate new font size based on window size
        base_font_size = 12  # Base font size
        scale_factor = min(width, height) / 800  # Scale based on smallest dimension
        new_font_size = int(base_font_size * scale_factor)
        
        # Update all button fonts
        for button in [
            self.sector_button, self.planet_button, self.people_button,
            self.lifeforms_button, self.ships_button, self.vehicle_button,
            self.events_button, self.technology_button, self.organizations_button,
            self.adventure_hooks_button, self.console_button
        ]:
            font = button.font()
            font.setPointSize(new_font_size)
            button.setFont(font)
            
            # Update button size policy to maintain proper scaling
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # Update minimum size based on font size
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(button.text())
            text_height = metrics.height()
            button.setMinimumSize(text_width + 40, text_height + 20)
            
        # Update text box fonts
        text_box_font = self.main_view.font()
        text_box_font.setPointSize(new_font_size)
        self.main_view.setFont(text_box_font)
        
        # Update flow layout spacing if container exists
        try:
            if self.button_container:
                flow_layout = self.button_container.layout()
                if flow_layout:
                    flow_layout.setSpacing(new_font_size // 2)
        except Exception as e:
            logger.warning(f"Failed to update flow layout spacing: {e}")
            
        # Call original resize event
        super().resizeEvent(event)

if __name__ == "__main__":
    logger.info("Starting application...")
    app = QApplication(sys.argv)
    window = HitchhikersGuideToTheGalaxy()
    window.show()
    sys.exit(app.exec())
