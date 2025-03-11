from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont
import sys
import os
import configparser
from dotenv import load_dotenv
from model.traveller_database import TravellerDatabase
from model.migrations import run_migrations
from controller.sectors_controller import SectorController
from controller.planets_controller import PlanetController
from controller.characters_controller import CharactersController
from controller.lifeforms_controller import LifeformsController
from controller.ships_controller import ShipsController
from controller.vehicals_controller import VehiclesController
from controller.events_controller import EventsController
from controller.technology_controller import TechnologyController
from controller.organizations_controller import OrganizationsController
from controller.adventure_hooks_controller import AdventureHooksController
from controller.SQLQueryController import SQLQueryController

# Define default stylesheets for light and dark themes
LIGHT_STYLESHEET = """
QMainWindow {
    background-color: white;
    color: black;
}
QTextEdit {
    background-color: #f0f0f0;
    color: black;
}
QPushButton {
    background-color: #e0e0e0;
    color: black;
}
"""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #2e2e2e;
    color: white;
}
QTextEdit {
    background-color: #4a4a4a;
    color: white;
}
QPushButton {
    background-color: #3a3a3a;
    color: white;
}
"""

# SettingsDialog for theme and font selection
class SettingsDialog(QDialog):
    def __init__(self, current_theme, current_font, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 150)
        layout = QVBoxLayout()

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Font selection
        font_layout = QHBoxLayout()
        font_label = QLabel("Font:")
        self.font_button = QPushButton("Choose Font")
        self.font_display = QLabel(current_font.family() + " " + str(current_font.pointSize()))
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_display)
        font_layout.addWidget(self.font_button)
        layout.addLayout(font_layout)

        self.font_button.clicked.connect(self.choose_font)

        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.setLayout(layout)
        self.selected_font = current_font

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.selected_font, self, "Select Font")
        if ok:
            self.selected_font = font
            self.font_display.setText(font.family() + " " + str(font.pointSize()))

class HitchhikersGuideToTheGalaxy(QMainWindow):
    def __init__(self):
        super().__init__()

        print("Initializing HitchhikersGuideToTheGalaxy window...")

        # Load environment variables and config file for defaults
        load_dotenv('config/.env', override=True)
        db_type = os.getenv('DATABASE_TYPE')
        print(f"Database type is: {db_type}")

        if db_type not in ['sqlite', 'mysql']:
            raise ValueError("Unsupported database type.")

        # Read defaults from config/.config
        config_parser = configparser.ConfigParser()
        config_parser.read('config/.config')
        default_theme = config_parser.get('Display', 'theme', fallback='Light').capitalize()
        default_width = config_parser.getint('Display', 'window_width', fallback=1024)
        default_height = config_parser.getint('Display', 'window_height', fallback=768)
        default_x = config_parser.getint('Display', 'window_x', fallback=100)
        default_y = config_parser.getint('Display', 'window_y', fallback=50)

        # Initialize QSettings to persist user settings
        self.qsettings = QSettings("YourCompany", "TASJ")

        # Load window geometry from QSettings or use defaults
        window_size = self.qsettings.value("windowSize", QSize(default_width, default_height))
        window_pos = self.qsettings.value("windowPos", QPoint(default_x, default_y))
        self.resize(window_size)
        self.move(window_pos)

        # Load theme and font from QSettings, falling back to defaults
        self.current_theme = self.qsettings.value("theme", default_theme)
        font_string = self.qsettings.value("font", "")
        if font_string:
            self.current_font = QFont()
            self.current_font.fromString(font_string)
        else:
            self.current_font = QFont("Arial", 10)

        # Apply the current theme
        self.apply_theme(self.current_theme)
        self.setFont(self.current_font)

        self.setWindowTitle("Hitchhikers Guide to the Galaxy")

        # Setup database connection
        db_instance = TravellerDatabase(db_type)

        # Initialize Controllers with db_instance
        self.sector_controller = SectorController(db_instance)
        self.planet_controller = PlanetController(db_instance)
        self.characters_controller = CharactersController(db_instance)
        self.lifeforms_controller = LifeformsController(db_instance)
        self.events_controller = EventsController(db_instance)
        self.organizations_controller = OrganizationsController(db_instance)
        self.adventure_hooks_controller = AdventureHooksController(db_instance)
        self.ships_controller = ShipsController(db_instance)
        self.vehicals_controller = VehiclesController(db_instance)
        self.technology_controller = TechnologyController(db_instance)
        self.sql_query_controller = SQLQueryController(db_instance)
        
        self.init_ui()

    def init_ui(self):
        print("Setting up UI...")
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # File Menu
        file_menu = menubar.addMenu("File")
        action_settings = QAction("Settings", self)
        file_menu.addAction(action_settings)
        action_settings.triggered.connect(self.open_settings)
        action_exit = QAction("Exit", self)
        file_menu.addAction(action_exit)
        action_exit.triggered.connect(self.close)

        # Database Menu
        db_menu = menubar.addMenu("Database")
        action_run_migrations = QAction("Run Migrations", self)
        db_menu.addAction(action_run_migrations)
        action_run_migrations.triggered.connect(self.run_migrations)
        action_run_sql = QAction("SQL Query", self)
        db_menu.addAction(action_run_sql)
        action_run_sql.triggered.connect(self.run_sql)
        
        # Use a tabbed interface for the various views
        self.tabs = QTabWidget()
        self.sector_view = QTextEdit()
        self.planet_view = QTextEdit()
        self.people_view = QTextEdit()
        self.lifeforms_view = QTextEdit()
        self.ships_view = QTextEdit()
        self.vehicals_view = QTextEdit()
        self.events_view = QTextEdit()
        self.technology_view = QTextEdit()
        self.organizations_view = QTextEdit()
        self.adventure_hooks_view = QTextEdit()
        
        self.tabs.addTab(self.sector_view, "Sectors")
        self.tabs.addTab(self.planet_view, "Planets")
        self.tabs.addTab(self.people_view, "People")
        self.tabs.addTab(self.lifeforms_view, "Lifeforms")
        self.tabs.addTab(self.ships_view, "Ships")
        self.tabs.addTab(self.vehicals_view, "Vehicles")
        self.tabs.addTab(self.events_view, "Events")
        self.tabs.addTab(self.technology_view, "Technology")
        self.tabs.addTab(self.organizations_view, "Organizations")
        self.tabs.addTab(self.adventure_hooks_view, "Adventure Hooks")
        
        # Lower text box for output/logs
        self.lower_text_box = QTextEdit(self)
        self.lower_text_box.setStyleSheet("background-color: #4a3b6e; color: white; padding: 10px;")
        self.lower_text_box.setReadOnly(True)
        
        # Create a main vertical layout that includes the tabs and lower text box
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.lower_text_box)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")
        print("UI setup complete.")

    def apply_theme(self, theme):
        if theme == "Dark":
            self.setStyleSheet(DARK_STYLESHEET)
        else:
            self.setStyleSheet(LIGHT_STYLESHEET)

    def open_settings(self):
        dialog = SettingsDialog(self.current_theme, self.current_font, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_theme = dialog.theme_combo.currentText()
            self.current_font = dialog.selected_font
            self.apply_theme(self.current_theme)
            # Set the font globally for all widgets
            QApplication.instance().setFont(self.current_font)
            # Optionally update the font for the main window if needed
            self.setFont(self.current_font)
            # Save the new settings persistently using QSettings
            self.qsettings.setValue("theme", self.current_theme)
            self.qsettings.setValue("font", self.current_font.toString())
            QMessageBox.information(self, "Settings", "Settings saved successfully.")

    def run_migrations(self):
        db_type = os.getenv('DATABASE_TYPE')
        run_migrations(db_type)
        QMessageBox.information(self, "Migrations", "Migrations have been run successfully.")
      
    def run_sql(self):
        self.sector_controller.show_view(self.lower_text_box)

    def show_sector(self):
        self.sector_controller.show_view(self.lower_text_box)

    def show_planet(self):
        self.planet_controller.show_view(self.lower_text_box)

    def show_people(self):
        self.characters_controller.show_view(self.lower_text_box)

    def show_lifeforms(self):
        self.lifeforms_controller.show_view(self.lower_text_box)

    def show_ships(self):
        self.ships_controller.show_view(self.lower_text_box)

    def show_technology(self):
        self.technology_controller.show_view(self.lower_text_box)

    def show_vehicals(self):
        self.vehicals_controller.show_view(self.lower_text_box)
        
    def show_events(self):
        self.events_controller.show_view(self.lower_text_box)
    
    def show_organizations(self):
        self.organizations_controller.show_view(self.lower_text_box)

    def show_adventure_hooks(self):
        self.adventure_hooks_controller.show_view(self.lower_text_box)

    def closeEvent(self, event):
        # Save window geometry on close using QSettings
        self.qsettings.setValue("windowPos", self.pos())
        self.qsettings.setValue("windowSize", self.size())
        super().closeEvent(event)

if __name__ == "__main__":
    print("Starting application...")
    app = QApplication(sys.argv)
    window = HitchhikersGuideToTheGalaxy()
    window.show()
    print("Showing window...")
    sys.exit(app.exec())
