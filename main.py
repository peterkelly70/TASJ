from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import *
import sys
import os
import configparser
from dotenv import load_dotenv
import multiprocessing
from model.traveller_database import TravellerDatabase
from model.migrations import run_migrations
from controller.data_download_controller import DataDownloadController

# Load environment variables
load_dotenv("config/.env")
DATABASE_TYPE = os.getenv("DATABASE_TYPE")
DATABASE_PATH = os.getenv("DATABASE_FILE_PATH")

# Theme styles
LIGHT_STYLESHEET = "QMainWindow { background-color: white; color: black; }"
DARK_STYLESHEET = "QMainWindow { background-color: #2e2e2e; color: white; }"

class SettingsDialog(QDialog):
    """Dialog for selecting theme and font."""
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
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Font selection
        font_layout = QHBoxLayout()
        font_label = QLabel("Font:")
        self.font_button = QPushButton("Choose Font")
        self.font_display = QLabel(f"{current_font.family()} {current_font.pointSize()}")
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_display)
        font_layout.addWidget(self.font_button)
        layout.addLayout(font_layout)

        self.selected_font = current_font
        self.font_button.clicked.connect(self.choose_font)

        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.setLayout(layout)

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.selected_font, self, "Select Font")
        if ok:
            self.selected_font = font
            self.font_display.setText(f"{font.family()} {font.pointSize()}")

class HitchhikersGuideToTheGalaxy(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing Hitchhiker's Guide to the Galaxy...")

        if DATABASE_TYPE not in ['sqlite', 'mysql']:
            raise ValueError("Unsupported database type.")

        # Read UI settings from config
        config_parser = configparser.ConfigParser()
        config_parser.read('config/.config')
        default_theme = config_parser.get('Display', 'theme', fallback='Light').capitalize()

        # Initialize settings persistence
        self.qsettings = QSettings("YourCompany", "TASJ")
        self.current_theme = self.qsettings.value("theme", default_theme)
        self.current_font = QFont("Arial", 10)

        # Load stored font settings
        font_string = self.qsettings.value("font", "")
        if font_string:
            self.current_font.fromString(font_string)

        # Initialize database and controllers
        self.db_instance = TravellerDatabase(DATABASE_TYPE)
        # Create progress queue and cancel event in main.py and pass to the controller.
        self.progress_queue = multiprocessing.Queue()
        self.cancel_event = multiprocessing.Event()
        self.data_download_controller = DataDownloadController(self.db_instance,
                                                               self.progress_queue,
                                                               self.cancel_event)

        # Setup UI
        self.setWindowTitle("Hitchhiker's Guide to the Galaxy")
        self.init_ui()
        self.apply_theme_and_font()

    def init_ui(self):
        print("Setting up UI...")
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)

        # File Menu
        file_menu = self.menubar.addMenu("File")
        action_settings = QAction("Settings", self)
        file_menu.addAction(action_settings)
        action_settings.triggered.connect(self.open_settings)
        action_exit = QAction("Exit", self)
        file_menu.addAction(action_exit)
        action_exit.triggered.connect(self.close)

        # Database Menu
        db_menu = self.menubar.addMenu("Database")
        action_run_migrations = QAction("Run Migrations", self)
        db_menu.addAction(action_run_migrations)
        action_run_migrations.triggered.connect(self.run_migrations)

        action_download_all = QAction("Download All Data", self)
        db_menu.addAction(action_download_all)
        action_download_all.triggered.connect(self.download_all_data)

        action_cancel_download = QAction("Cancel Download", self)
        db_menu.addAction(action_cancel_download)
        action_cancel_download.triggered.connect(self.cancel_download)

        # Progress Bar & Cancel Button
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_button)

        progress_container = QWidget()
        progress_container.setLayout(progress_layout)
        self.menubar.setCornerWidget(progress_container, Qt.TopRightCorner)

        # Tabbed UI
        self.tabs = QTabWidget()
        self.tabs.addTab(QTextEdit(), "Sectors")
        self.tabs.addTab(QTextEdit(), "Planets")
        self.tabs.addTab(QTextEdit(), "People")
        self.tabs.addTab(QTextEdit(), "Lifeforms")
        self.tabs.addTab(QTextEdit(), "Ships")
        self.tabs.addTab(QTextEdit(), "Vehicles")
        self.tabs.addTab(QTextEdit(), "Events")
        self.tabs.addTab(QTextEdit(), "Technology")
        self.tabs.addTab(QTextEdit(), "Organizations")
        self.tabs.addTab(QTextEdit(), "Adventure Hooks")

        # Log Output
        self.lower_text_box = QTextEdit(self)
        self.lower_text_box.setReadOnly(True)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.lower_text_box)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Timer for checking progress updates
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)

        self.statusBar().showMessage("Ready")
        print("UI setup complete.")

    def apply_theme_and_font(self):
        """Applies the selected theme and font globally."""
        base_sheet = DARK_STYLESHEET if self.current_theme == "Dark" else LIGHT_STYLESHEET
        font_override = f"QMainWindow, QMenuBar, QTabWidget, QPushButton, QTextEdit, QLabel, QComboBox, QDialogButtonBox {{ font-family: \"{self.current_font.family()}\"; font-size: {self.current_font.pointSize()}pt; }}"
        self.setStyleSheet(base_sheet + font_override)
        QApplication.instance().setFont(self.current_font)

    def download_all_data(self):
        """Starts the download in a background process and updates UI."""
        self.lower_text_box.append("🚀 Downloading all data...")
        self.data_download_controller.start_download(self.lower_text_box,
                                                     self.progress_bar,
                                                     self.cancel_button)
        self.progress_timer.start(500)  # Update progress every 500ms
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)

    def cancel_download(self):
        """Cancels an ongoing download process and updates UI."""
        self.lower_text_box.append("⏹️ Cancelling download...")
        self.data_download_controller.cancel_download(self.lower_text_box)
        self.progress_timer.stop()
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(False)

    def update_progress(self):
        """Updates progress bar based on background task messages."""
        message = ""  # Ensure `message` is always defined.
        while not self.data_download_controller.progress_queue.empty():
            message = self.data_download_controller.progress_queue.get()
            self.lower_text_box.append(message)

            if "Progress:" in message:
                try:
                    progress_text = message.split(":")[1].strip().split("/")
                    current, total = int(progress_text[0]), int(progress_text[1])
                    percentage = int((current / total) * 100)
                    self.progress_bar.setValue(percentage)
                except ValueError:
                    pass

        if message and "Download complete" in message:
            self.progress_timer.stop()
            self.progress_bar.setValue(100)
            self.cancel_button.setEnabled(False)

    def run_migrations(self):
        """Runs database migrations."""
        try:
            run_migrations(DATABASE_TYPE)
            self.lower_text_box.append("✅ Database migrations completed successfully.")
        except Exception as e:
            self.lower_text_box.append(f"❌ Error running migrations: {str(e)}")

    def open_settings(self):
        """Opens the settings dialog and applies changes globally."""
        dialog = SettingsDialog(self.current_theme, self.current_font, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_theme = dialog.theme_combo.currentText()
            self.current_font = dialog.selected_font
            self.qsettings.setValue("theme", self.current_theme)
            self.qsettings.setValue("font", self.current_font.toString())
            self.apply_theme_and_font()
            QMessageBox.information(self, "Settings", "Settings applied successfully.")

if __name__ == "__main__":
    print("Starting application...")
    app = QApplication(sys.argv)
    window = HitchhikersGuideToTheGalaxy()
    window.show()
    sys.exit(app.exec())
