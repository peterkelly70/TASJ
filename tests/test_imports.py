import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestControllerImports(unittest.TestCase):

    def test_imports(self):
        """Test that all controller modules can be imported without errors."""
        try:
            from controller.adventure_hooks_controller import AdventureHooksController
            from controller.control_controller import ControlController
            from controller.data_download_controller import DataDownloadController
            from controller.events_controller import EventsController
            from controller.font_controller import FontController
            from controller.lifeforms_controller import LifeformsController
            from controller.organizations_controller import OrganizationsController
            from controller.people_controller import PeopleController
            from controller.planets_controller import PlanetsController
            from controller.sectors_controller import SectorsController
            from controller.ships_controller import ShipsController
            from controller.technology_controller import TechnologyController
            from controller.theme_controller import ThemeController
            from controller.vehicals_controller import VehicalsController
        except ImportError as e:
            self.fail(f"Failed to import one or more controllers: {e}")
        except NameError as e:
             self.fail(f"NameError during controller import: {e}")
        except Exception as e:
            self.fail(f"An unexpected error occurred during controller import: {e}")

if __name__ == '__main__':
    unittest.main()
