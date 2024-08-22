from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
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

class HitchhikersGuideToTheGalaxy(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hitchhikers Guide to the Galaxy")
        self.setGeometry(100, 100, 800, 600)

        # Initialize Controllers
        self.sector_controller = SectorController()
        self.planet_controller = PlanetController()
        self.characters_controller = CharactersController()
        self.lifeforms_controller = LifeformsController()
        self.events_controller = EventsController()
        self.organizations_controller = OrganizationsController()
        self.adventure_hooks_controller = AdventureHooksController()
        self.ships_controller = ShipsController()
        self.vehicals_controller = VehiclesController()
        self.technology_controller = TechnologyController()

        self.init_ui()

    def init_ui(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File Menu")
        action_exit = QAction("Exit", self)
        file_menu.addAction(action_exit)
        action_exit.triggered.connect(self.close)

        # Main Interface (buttons)
        button_layout = QHBoxLayout()
        self.sector_button = QPushButton("Sector")
        self.planet_button = QPushButton("Planet")
        self.people_button = QPushButton("People")
        self.lifeforms_button = QPushButton("Lifeforms")
        self.events_button = QPushButton("Events")
        self.organizations_button = QPushButton("Organisations")
        self.adventure_hooks_button = QPushButton("Adventure Hooks")
        self.ships_button = QPushButton("Ships")
        self.vehicals_button = QPushButton("Vehicals")
        self.technology_button = QPushButton("Technology")
        
        button_layout.addWidget(self.sector_button)
        button_layout.addWidget(self.planet_button)
        button_layout.addWidget(self.lifeforms_button)
        button_layout.addWidget(self.people_button)
        button_layout.addWidget(self.organizations_button)
        button_layout.addWidget(self.events_button)
        button_layout.addWidget(self.adventure_hooks_button)
        button_layout.addWidget(self.ships_button)
        button_layout.addWidget(self.vehicals_button)
        button_layout.addWidget(self.technology_button)
        

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(button_layout)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.lower_text_box = QTextEdit(self)
        self.lower_text_box.setStyleSheet("background-color: #4a3b6e; color: white; padding: 10px;")
        self.lower_text_box.setReadOnly(True)
        self.main_layout.addWidget(self.lower_text_box)

        self.statusBar().showMessage("Ready")

        # Connect buttons to controllers
        self.sector_button.clicked.connect(self.show_sector)
        self.planet_button.clicked.connect(self.show_planet)
        self.people_button.clicked.connect(self.show_people)
        self.lifeforms_button.clicked.connect(self.show_lifeforms)
        self.ships_button.clicked.connect(self.show_ships)
        self.vehicals_button.clicked.connect(self.show_vehicals)
        self.events_button.clicked.connect(self.show_events)
        self.technology_button.clicked.connect(self.show_technology)
        self.organizations_button.clicked.connect(self.show_organizations)
        self.adventure_hooks_button.clicked.connect(self.show_adventure_hooks)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HitchhikersGuideToTheGalaxy()
    window.show()
    sys.exit(app.exec())
