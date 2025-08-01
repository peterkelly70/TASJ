"""
Test cases for the PlanetDB class.
"""
import unittest
from unittest.mock import Mock, patch
from model.planet import Planet
from model.planets_db import PlanetDB

class TestPlanetDB(unittest.TestCase):
    """Test cases for the PlanetDB class."""

    def setUp(self):
        """Set up test data and mocks."""
        # Create a mock database instance
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
            "image_path": "",
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
    
    def test_create_planet_success(self):
        """Test creating a planet successfully."""
        # Setup
        planet = Planet(**self.sample_planet_data)
        self.mock_db.create_record.return_value = 42  # Mock the created planet ID
        
        # Execute
        result = self.planet_db.create_planet(planet)
        
        # Verify
        self.assertEqual(result, 42)
        self.mock_db.create_record.assert_called_once()
        
        # Get the arguments passed to create_record
        args, kwargs = self.mock_db.create_record.call_args
        self.assertEqual(args[0], "planets")  # First arg should be table name
        
        # Verify the data passed to create_record
        data = args[1] if len(args) > 1 else kwargs
        self.assertEqual(data["name"], "Terra")
        self.assertEqual(data["sector_id"], 1)
        self.assertNotIn("planet_id", data)  # Should be removed for new records
    
    def test_create_planet_validation_failure(self):
        """Test creating a planet with invalid data."""
        # Setup - create a planet with missing required fields
        invalid_planet = Planet(name=None, sector_id=None, x_coordinate=None, y_coordinate=None)
        
        # Execute
        result = self.planet_db.create_planet(invalid_planet)
        
        # Verify
        self.assertIsNone(result)
        self.mock_db.create_record.assert_not_called()
    
    def test_get_planet(self):
        """Test retrieving a planet by ID."""
        # Setup
        planet_data = self.sample_planet_data.copy()
        planet_data["planet_id"] = 42
        self.mock_db.read_records.return_value = [planet_data]
        
        # Execute
        result = self.planet_db.get_planet(42)
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Terra")
        self.assertEqual(result.planet_id, 42)
        self.mock_db.read_records.assert_called_once_with("planets", {"planet_id": 42}, limit=1)
    
    def test_get_planet_not_found(self):
        """Test retrieving a non-existent planet."""
        # Setup
        self.mock_db.read_records.return_value = []
        
        # Execute
        result = self.planet_db.get_planet(999)
        
        # Verify
        self.assertIsNone(result)
        self.mock_db.read_records.assert_called_once()
    
    def test_get_planets_by_sector(self):
        """Test retrieving all planets in a sector."""
        # Setup
        planet1 = self.sample_planet_data.copy()
        planet1["planet_id"] = 1
        planet2 = self.sample_planet_data.copy()
        planet2.update({"planet_id": 2, "name": "Mars"})
        
        self.mock_db.read_records.return_value = [planet1, planet2]
        
        # Execute
        result = self.planet_db.get_planets_by_sector(1)
        
        # Verify
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "Terra")
        self.assertEqual(result[1].name, "Mars")
        self.mock_db.read_records.assert_called_once_with("planets", {"sector_id": 1})
    
    def test_update_planet(self):
        """Test updating a planet."""
        # Setup
        planet = Planet(planet_id=42, **self.sample_planet_data)
        self.mock_db.update_record.return_value = True
        
        # Execute
        result = self.planet_db.update_planet(planet)
        
        # Verify
        self.assertTrue(result)
        self.mock_db.update_record.assert_called_once()
        
        # Get the arguments passed to update_record
        args, kwargs = self.mock_db.update_record.call_args
        self.assertEqual(args[0], "planets")  # First arg should be table name
        
        # Verify the data passed to update_record
        data = args[1] if len(args) > 1 else kwargs
        self.assertEqual(data["name"], "Terra")
        self.assertEqual(data["sector_id"], 1)
        self.assertEqual(data["planet_id"], 42)  # Should include planet_id for updates
    
    def test_delete_planet(self):
        """Test deleting a planet."""
        # Setup
        self.mock_db.delete_record.return_value = True
        
        # Execute
        result = self.planet_db.delete_planet(42)
        
        # Verify
        self.assertTrue(result)
        self.mock_db.delete_record.assert_called_once_with("planets", {"planet_id": 42})

if __name__ == "__main__":
    unittest.main()
