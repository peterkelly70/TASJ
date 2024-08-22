import unittest
from PyQt5.QtWidgets import QApplication
from main import HitchhikersGuideToTheGalaxy

class TestHitchhikersGuideToTheGalaxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])  # Create a QApplication for the tests

    def setUp(self):
        self.window = HitchhikersGuideToTheGalaxy()  # Create the main window

    def test_sector_button(self):
        self.window.sector_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Sector button has been pushed")

    def test_planet_button(self):
        self.window.planet_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Planet button has been pushed")

    def test_people_button(self):
        self.window.people_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Characters button has been pushed")

    def test_lifeforms_button(self):
        self.window.lifeforms_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Lifeforms button has been pushed")

    def test_ships_button(self):
        self.window.ships_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Ships button has been pushed")

    def test_vehicals_button(self):
        self.window.vehicals_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Vehicles button has been pushed")

    def test_events_button(self):
        self.window.events_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Events button has been pushed")

    def test_technology_button(self):
        self.window.technology_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Technology button has been pushed")

    def test_organizations_button(self):
        self.window.organizations_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Organizations button has been pushed")

    def test_adventure_hooks_button(self):
        self.window.adventure_hooks_button.click()
        self.assertEqual(self.window.lower_text_box.toPlainText(), "Adventure Hooks button has been pushed")

    def tearDown(self):
        self.window.close()  # Clean up the window after each test

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()  # Quit the QApplication after all tests

if __name__ == "__main__":
    unittest.main()
