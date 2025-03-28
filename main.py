from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QProgressBar, QMenuBar, QTabWidget,
    QTextEdit, QDialogButtonBox, QWidget, QFontDialog, QMessageBox, QMenu,
    QListWidget, QGroupBox, QFormLayout, QListWidgetItem
)
from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QFontMetrics
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

from model.traveller_database import TravellerDatabase
from model.migrations import run_migrations
from controller.data_download_controller import DataDownloadController
from controller.font_controller import FontController
from font_manager import FontManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure file handler with rotation
log_file = os.path.join('logs', 'tasj.log')
os.makedirs('logs', exist_ok=True)
file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Load environment variables
load_dotenv("config/.env")
DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
DATABASE_PATH: str = os.getenv("DATABASE_FILE_PATH", "database/traveller_campaign.db")

# Theme styles
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
    """Dialog for selecting theme and font settings.
    
    Attributes:
        current_theme (str): The currently selected theme
        current_font (QFont): The currently selected font
        selected_font (QFont): The newly selected font (if any)
        theme_combo (QComboBox): Dropdown for theme selection
        font_display (QLabel): Label showing current font details
    """
    
    def __init__(self, current_theme: str, current_font: QFont, parent: Optional[QMainWindow] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 150)
        
        self._setup_ui(current_theme, current_font)
        
    def _setup_ui(self, current_theme: str, current_font: QFont) -> None:
        """Set up the UI components of the settings dialog."""
        layout = QVBoxLayout()
        self._setup_theme_selection(layout, current_theme)
        self._setup_font_selection(layout, current_font)
        self._setup_buttons(layout)
        self.setLayout(layout)
        
    def _setup_theme_selection(self, layout: QVBoxLayout, current_theme: str) -> None:
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText(current_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
    def _setup_font_selection(self, layout: QVBoxLayout, current_font: QFont) -> None:
        font_layout = QHBoxLayout()
        font_label = QLabel("Font:")
        self.font_button = QPushButton("Choose Font")
        self.font_display = QLabel(f"{current_font.family()} {current_font.pointSize()}")
        self.selected_font = current_font
        
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_display)
        font_layout.addWidget(self.font_button)
        layout.addLayout(font_layout)
        
        self.font_button.clicked.connect(self.choose_font)

    def _setup_buttons(self, layout: QVBoxLayout) -> None:
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def choose_font(self) -> None:
        font, ok = QFontDialog.getFont(self.selected_font, self, "Select Font")
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
        super().__init__()
        logger.info("Initializing Hitchhiker's Guide to the Galaxy...")
        
        try:
            self._initialize_database()
            self._load_settings()
            self._initialize_controllers()
            self._setup_ui()
            self.apply_theme_and_font()
            logger.info("Application initialized successfully")
            
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
        
    def _load_settings(self) -> None:
        """Load and initialize application settings."""
        config_parser = configparser.ConfigParser()
        config_parser.read('config/.config')
        default_theme = config_parser.get('Display', 'theme', fallback='Light').capitalize()
        
        self.qsettings = QSettings("YourCompany", "TASJ")
        self.current_theme = self.qsettings.value("theme", default_theme)
        self.current_font = QFont("Arial", 10)
        
        font_string = self.qsettings.value("font", "")
        if font_string:
            self.current_font.fromString(font_string)

        # Restore window geometry
        geometry = self.qsettings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size if no saved geometry
            self.resize(1024, 768)
            self.center_window()
            
        logger.info(f"Settings loaded - Theme: {self.current_theme}")

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
        self.font_controller = FontController()
        self.data_download_controller = DataDownloadController(
            self.db_instance,
            multiprocessing.Queue(),
            multiprocessing.Event()
        )
        
    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        self.setWindowTitle("Hitchhiker's Guide to the Galaxy")
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        # Licenses action
        licenses_action = QAction("Licenses", self)
        licenses_action.triggered.connect(self.open_licenses)
        file_menu.addAction(licenses_action)
        
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
        
        # Create main interface
        button_layout = QHBoxLayout()
        
        # Create buttons
        self.sector_button = QPushButton("Sectors")
        self.planet_button = QPushButton("Planets")
        self.people_button = QPushButton("Characters")
        self.lifeforms_button = QPushButton("Lifeforms")
        self.ships_button = QPushButton("Ships")
        self.vehicals_button = QPushButton("Vehicles")
        self.events_button = QPushButton("Events")
        self.technology_button = QPushButton("Technology")
        self.organizations_button = QPushButton("Organizations")
        self.adventure_hooks_button = QPushButton("Adventure Hooks")
        
        # Add buttons to layout
        buttons = [
            self.sector_button, self.planet_button, self.people_button,
            self.lifeforms_button, self.ships_button, self.vehicals_button,
            self.events_button, self.technology_button, self.organizations_button,
            self.adventure_hooks_button
        ]
        
        for button in buttons:
            button_layout.addWidget(button)
            button.clicked.connect(self._create_button_handler(button.text()))
        
        main_layout.addLayout(button_layout)
        
        # Create text box for output
        self.lower_text_box = QTextEdit()
        self.lower_text_box.setReadOnly(True)
        main_layout.addWidget(self.lower_text_box)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        # Create cancel button (initially disabled)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        main_layout.addWidget(self.cancel_button)
        
    def _create_button_handler(self, button_text: str):
        def handler():
            self.lower_text_box.append(f"{button_text} button has been pushed")
        return handler
        
    def apply_theme_and_font(self) -> None:
        """Apply the current theme and font settings."""
        # Load theme
        theme_file = f"config/themes/{self.current_theme.lower()}.theme"
        if not os.path.exists(theme_file):
            logger.error(f"Theme file not found: {theme_file}")
            return

        # Get theme-specific font if no custom font set
        if not self.current_font:
            theme_font_id = self.current_theme.lower()
            self.current_font = self.font_controller.ensure_font_available(theme_font_id, self)
            if not self.current_font:
                # Fallback to system font if download failed or was declined
                self.current_font = QFont("DejaVu Sans", 10)
        
        # Load and apply theme
        config = configparser.ConfigParser()
        config.read(theme_file)

        # Apply styles from theme file
        if 'Styles' in config:
            style_sheet = ""
            for selector, style in config['Styles'].items():
                style_sheet += f"{selector} {style}\n"
            self.setStyleSheet(style_sheet)

        # Apply font
        self.setFont(self.current_font)
        for widget in self.findChildren(QWidget):
            widget.setFont(self.current_font)
            
    def download_all_data(self) -> None:
        """Start downloading data in background process."""
        logger.info("Starting data download process")
        try:
            self.data_download_controller.start_download()
            self._setup_progress_monitoring()
        except Exception as e:
            logger.error(f"Failed to start data download: {str(e)}", exc_info=True)
            
    def cancel_download(self) -> None:
        """Cancel ongoing download process."""
        logger.info("Cancelling data download")
        self.data_download_controller.cancel_event.set()
        
    def run_migrations(self) -> None:
        """Execute database migrations."""
        logger.info("Running database migrations")
        try:
            run_migrations(self.db_instance)
            logger.info("Migrations completed successfully")
            QMessageBox.information(self, "Success", "Database migrations completed successfully.")
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Migration failed: {str(e)}")
            
    def _setup_progress_monitoring(self) -> None:
        """Set up progress monitoring for background tasks."""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)
        
    def update_progress(self) -> None:
        """Updates progress bar based on background task messages."""
        while not self.data_download_controller.progress_queue.empty():
            message = self.data_download_controller.progress_queue.get()
            self.lower_text_box.append(message)
            
            if "Progress:" in message:
                try:
                    progress = int(message.split(":")[1].strip())
                    self.progress_bar.setValue(progress)
                except (IndexError, ValueError):
                    logger.warning(f"Invalid progress message format: {message}")
                    
            if "Download complete" in message:
                self.progress_timer.stop()
                self.progress_bar.setValue(100)
                self.cancel_button.setEnabled(False)
                
    def open_settings(self) -> None:
        """Opens the settings dialog and applies changes globally."""
        dialog = SettingsDialog(self.current_theme, self.current_font, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_theme = dialog.theme_combo.currentText()
            self.current_font = dialog.selected_font
            self.qsettings.setValue("theme", self.current_theme)
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
            # Create and show progress UI
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)
            
            # Start download with UI elements
            self.data_download_controller.start_download(
                view_widget=self.lower_text_box,
                progress_bar=self.progress_bar,
                cancel_button=self.cancel_button
            )
        except Exception as e:
            logger.error(f"API data download failed: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download API data: {str(e)}")
            self.progress_bar.setVisible(False)
            self.cancel_button.setEnabled(False)

    def open_licenses(self) -> None:
        """Opens the licenses dialog."""
        self.font_controller.show_licenses(self)

if __name__ == "__main__":
    logger.info("Starting application...")
    app = QApplication(sys.argv)
    window = HitchhikersGuideToTheGalaxy()
    window.show()
    sys.exit(app.exec())
