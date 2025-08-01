import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QProgressBar,
    QTextEdit, QMenuBar, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QCloseEvent

from controller.settings_controller import SettingsController
from controller.theme_controller import ThemeController
from controller.font_controller import FontController
from controller.data_download_controller import DataDownloadController
from controller.mission_generator_controller import MissionGeneratorController
from controller.adventure_hooks_controller import AdventureHooksController

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(
        self,
        settings_controller: SettingsController,
        theme_controller: ThemeController,
        font_controller: FontController,
        data_controller: DataDownloadController
    ) -> None:
        super().__init__()
        
        self.settings_controller = settings_controller
        self.theme_controller = theme_controller
        self.font_controller = font_controller
        self.data_controller = data_controller
        
        # Initialize game tools controllers
        self.mission_generator_controller = MissionGeneratorController(parent_widget=self)
        self.adventure_hooks_controller = AdventureHooksController(parent_widget=self)
        
        self._setup_ui()
        self._restore_settings()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Traveller Campaign Management")
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self._setup_menu_bar()
        
        # Create main content area
        self._setup_content_area(layout)
        
        # Create status bar with progress
        self._setup_status_bar()
        
        # Set up progress update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(100)
        
    def _setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        licenses_action = QAction("Licenses", self)
        licenses_action.triggered.connect(self.open_licenses)
        file_menu.addAction(licenses_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit Application", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        mission_generator_action = QAction("Mission Generator", self)
        mission_generator_action.triggered.connect(self.open_mission_generator)
        tools_menu.addAction(mission_generator_action)
        
        adventure_hooks_action = QAction("Adventure Hooks", self)
        adventure_hooks_action.triggered.connect(self.open_adventure_hooks)
        tools_menu.addAction(adventure_hooks_action)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        
        available_themes = self.theme_controller.get_available_themes()
        logger.info(f"Setting up theme menu. Found themes: {available_themes}")
        
        if not available_themes:
            logger.warning("No themes found to populate the menu!")
            no_themes_action = QAction("No themes found", self)
            no_themes_action.setEnabled(False)
            theme_menu.addAction(no_themes_action)
        else:
            for theme in available_themes:
                logger.debug(f"Processing theme for menu: '{theme}'")
                try:
                    # Create action with capitalized title
                    action_title = theme.title()
                    theme_action = QAction(action_title, self)
                    logger.debug(f"  Created QAction with title: '{action_title}'")
                    
                    # Use lambda with default argument to capture current theme name
                    theme_action.triggered.connect(lambda checked, t=theme: self.change_theme(t))
                    logger.debug(f"  Connected trigger for theme: '{theme}'")
                    
                    # Add action to the menu
                    theme_menu.addAction(theme_action)
                    logger.debug(f"  Successfully added action '{action_title}' to theme menu")
                    
                except Exception as e:
                    logger.error(f"Error processing theme '{theme}' for menu: {e}", exc_info=True)
        
        theme_menu.addSeparator()
        
        font_action = QAction("Custom Font...", self)
        font_action.triggered.connect(self.choose_font)
        theme_menu.addAction(font_action)
        
    def _setup_content_area(self, layout: QVBoxLayout) -> None:
        """Set up the main content area."""
        # Create a tab widget for main content
        self.content_tabs = QTabWidget()
        layout.addWidget(self.content_tabs)
        
        # Add a welcome tab
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_label = QLabel("Welcome to Traveller Campaign Management")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.content_tabs.addTab(welcome_widget, "Welcome")
        
    def _setup_status_bar(self) -> None:
        """Set up the status bar with progress indicator."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setVisible(False)
        self.statusBar().addPermanentWidget(self.cancel_button)
        
    def _restore_settings(self) -> None:
        """Restore saved settings."""
        # Restore window geometry
        geometry = self.settings_controller.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
            
        # Restore theme
        theme = self.settings_controller.load_theme()
        self.change_theme(theme)
        
        # Restore custom font if any
        font = self.settings_controller.load_font()
        if font:
            self.theme_controller.set_custom_font(font)
            
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event."""
        # Save window geometry
        self.settings_controller.save_window_geometry(self.saveGeometry())
        event.accept()
        
    def change_theme(self, theme_name: str) -> None:
        """Change the application theme."""
        stylesheet = self.theme_controller.load_stylesheet(theme_name)
        if stylesheet is not None: 
            self.setStyleSheet(stylesheet)
            logger.info(f"Applied theme: {theme_name}")
        else:
            logger.error(f"Could not load stylesheet for theme: {theme_name}. Applying empty stylesheet.")
            self.setStyleSheet("") 
        self.settings_controller.save_theme(theme_name)
        
    def choose_font(self) -> None:
        """Open custom font selection dialog."""
        current_font = self.theme_controller.get_current_font() or QFont()
        
        font, ok = self.font_controller.get_font(current_font, self)
        
        if ok and font:
            logger.info(f"Custom font selected: {font.family()} {font.pointSize()}pt")
            self.theme_controller.set_custom_font(font)
            self.settings_controller.save_font(font)
            # Reapply current theme to update fonts immediately
            self.change_theme(self.settings_controller.load_theme()) # Use saved theme
        else:
            logger.info("Custom font selection cancelled or failed.")

    def open_settings(self) -> None:
        """Open settings dialog."""
        # TODO: Implement settings dialog
        pass
        
    def open_licenses(self) -> None:
        """Open licenses dialog."""
        self.font_controller.show_licenses(self)
        
    def open_mission_generator(self) -> None:
        """Open the mission generator in the main content area."""
        mission_widget = self.mission_generator_controller.get_widget()
        
        # Check if the tab already exists
        for i in range(self.content_tabs.count()):
            if self.content_tabs.tabText(i) == "Mission Generator":
                self.content_tabs.setCurrentIndex(i)
                return
        
        # Add a new tab if it doesn't exist
        self.content_tabs.addTab(mission_widget, "Mission Generator")
        self.content_tabs.setCurrentWidget(mission_widget)
        
    def open_adventure_hooks(self) -> None:
        """Open the adventure hooks generator in the main content area."""
        hooks_widget = self.adventure_hooks_controller.get_widget()
        
        # Check if the tab already exists
        for i in range(self.content_tabs.count()):
            if self.content_tabs.tabText(i) == "Adventure Hooks":
                self.content_tabs.setCurrentIndex(i)
                return
        
        # Add a new tab if it doesn't exist
        self.content_tabs.addTab(hooks_widget, "Adventure Hooks")
        self.content_tabs.setCurrentWidget(hooks_widget)
        
    def download_all_data(self) -> None:
        """Start downloading data in background process."""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        self.data_controller.start_download()
        
    def cancel_download(self) -> None:
        """Cancel ongoing download process."""
        self.data_controller.cancel_download()
        self.cancel_button.setEnabled(False)
        
    def update_progress(self) -> None:
        """Update progress bar based on background task messages."""
        while not self.data_controller.progress_queue.empty():
            message = self.data_controller.progress_queue.get()
            # TODO: Update progress display
            if "Progress:" in message:
                try:
                    progress = int(message.split(":")[1].strip().rstrip("%"))
                    self.progress_bar.setValue(progress)
                except ValueError:
                    pass
            elif "Complete" in message:
                self.progress_bar.setVisible(False)
                self.cancel_button.setVisible(False)
                QMessageBox.information(self, "Download Complete", 
                    "All data has been downloaded successfully.")

    def apply_theme_and_font(self) -> None:
        """Applies the theme and font loaded from settings."""
        # This method might be better placed in a controller or called via controller
        theme_name = self.settings_controller.load_theme()
        font = self.settings_controller.load_font()

        logger.info(f"Applying settings - Theme: {theme_name}, Font: {font}")

        # Apply Theme
        stylesheet = self.theme_controller.load_stylesheet(theme_name)
        if stylesheet is not None: # Check if loading was successful (empty string is success but no style)
            self.setStyleSheet(stylesheet)
            logger.info(f"Applied theme: {theme_name} on startup")
        else:
            logger.error(f"Could not load stylesheet for theme: {theme_name}. Applying empty stylesheet.")
            self.setStyleSheet("") # Apply empty/default stylesheet

        # Apply Font
        if font:
            self.theme_controller.set_custom_font(font)
