import unittest
from unittest.mock import Mock, patch
from model.planet import Planet
from model.planets_db import PlanetDB

class TestPlanetModel(unittest.TestCase):
    """Test cases for the Planet model and PlanetDB class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.planet_db = PlanetDB(self.mock_db)
        
        # Sample planet data
        self.sample_planet_data = {
            "name": "Terra",
            "sector_id": 1,
            "x_coordinate": 10,
            "y_coordinate": 20,
            "uwp": "A123456-7",
            "description": "Homeworld of the Third Imperium",
            "starport": "A",
            "size": "8",
            "atmosphere": "5",
            "hydrographics": "5",
            "population": "9",
            "government": "6",
            "law_level": "4",
            "tech_level": "C",
            "gas_giant": False,
            "bases": "Naval, Scout",
            "trade_codes": "Hi In Na",
            "travel_code": "Amber",
            "hex": "0101"
        }
    
    def test_planet_creation(self):
        """Test creating a Planet instance with valid data."""
        planet = Planet(**self.sample_planet_data)
        
        self.assertEqual(planet.name, "Terra")
        self.assertEqual(planet.sector_id, 1)
        self.assertEqual(planet.uwp, "A123456-7")
        self.assertEqual(planet.gas_giant, False)
    
    def test_planet_validation_valid(self):
        """Test planet data validation with valid data."""
        planet = Planet(**self.sample_planet_data)
        print(f"Validating planet: {planet}")
        errors = planet.validate()
        if errors:
            print(f"Validation errors: {errors}")
        self.assertEqual(len(errors), 0, f"Expected no validation errors, but got: {errors}")
    
    def test_planet_validation_invalid_uwp(self):
        """Test planet data validation with invalid UWP."""
        invalid_data = self.sample_planet_data.copy()
        invalid_data["uwp"] = "INVALID"
        planet = Planet(**invalid_data)
        
        errors = planet.validate()
        self.assertGreater(len(errors), 0)
        self.assertIn("UWP", errors[0])
    
    def test_planet_validation_missing_name(self):
        """Test planet data validation with missing name."""
        invalid_data = self.sample_planet_data.copy()
        del invalid_data["name"]
        planet = Planet(**invalid_data)
        
        errors = planet.validate()
        self.assertIn("name is required", errors[0].lower())
    
    @patch.object(PlanetDB, 'create_planet')
    def test_create_planet_success(self, mock_create):
        """Test successful planet creation."""
        # Setup
        planet = Planet(**self.sample_planet_data)
        expected_id = 42
        mock_create.return_value = expected_id
        
        # Execute
        result = self.planet_db.create_planet(planet)
        
        # Verify
        self.assertEqual(result, expected_id)
        mock_create.assert_called_once()
    
    @patch.object(PlanetDB, 'get_planet')
    def test_get_planet(self, mock_get):
        """Test retrieving a planet by ID."""
        # Setup
        expected_planet = Planet(**self.sample_planet_data)
        mock_get.return_value = expected_planet
        
        # Execute
        result = self.planet_db.get_planet(42)
        
        # Verify
        self.assertEqual(result.name, expected_planet.name)
        mock_get.assert_called_once_with(42)
    
    @patch.object(PlanetDB, 'get_planets_by_sector')
    def test_get_planets_by_sector(self, mock_get):
        """Test retrieving planets by sector."""
        # Setup
        planet1 = Planet(**self.sample_planet_data)
        planet2 = Planet(**{**self.sample_planet_data, "name": "Mars"})
        mock_get.return_value = [planet1, planet2]
        
        # Execute
        results = self.planet_db.get_planets_by_sector(1)
        
        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Terra")
        self.assertEqual(results[1].name, "Mars")
        mock_get.assert_called_once_with(1)
    
    @patch.object(PlanetDB, 'update_planet')
    def test_update_planet(self, mock_update):
        """Test updating a planet."""
        # Setup
        planet = Planet(**self.sample_planet_data, planet_id=42)
        mock_update.return_value = True
        
        # Execute
        result = self.planet_db.update_planet(planet)
        
        # Verify
        self.assertTrue(result)
        mock_update.assert_called_once_with(planet)
    
    @patch.object(PlanetDB, 'delete_planet')
    def test_delete_planet(self, mock_delete):
        """Test deleting a planet."""
        # Setup
        planet_id = 42
        mock_delete.return_value = True
        
        # Execute
        result = self.planet_db.delete_planet(planet_id)
        
        # Verify
        self.assertTrue(result)
        mock_delete.assert_called_once_with(planet_id)

if __name__ == '__main__':
    unittest.main()
