"""
Test cases for the Planet model to improve test coverage.
"""
import unittest
from model.planet import Planet

class TestPlanetCoverage(unittest.TestCase):
    """Test cases for the Planet model to improve test coverage."""

    def setUp(self):
        """Set up test data."""
        self.valid_planet_data = {
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
            "allegiance": "",
            "stellar": "",
            "gas_giant": False,
            "bases": "Naval, Scout",
            "trade_codes": "Hi In Na",
            "travel_code": "Amber",
            "importance": "",
            "economic": "",
            "hex": "0101",
            "subsector_id": None,
            "travel_zone": "",
            "pbg": ""
        }

    def test_planet_creation_with_optional_fields(self):
        """Test creating a planet with optional fields."""
        # Test with all optional fields
        planet = Planet(**self.valid_planet_data)
        self.assertEqual(planet.name, "Terra")
        self.assertEqual(planet.uwp, "A123456-7")
        self.assertEqual(planet.tech_level, "C")
        self.assertFalse(planet.gas_giant)

    def test_planet_validation_without_optional_fields(self):
        """Test planet validation with only required fields."""
        # Create a planet with only required fields
        minimal_planet = Planet(
            name="Minimal",
            sector_id=1,
            x_coordinate=5,
            y_coordinate=5
        )
        errors = minimal_planet.validate()
        self.assertEqual(len(errors), 0, f"Expected no validation errors, but got: {errors}")

    def test_planet_validation_invalid_coordinates(self):
        """Test planet validation with invalid coordinates."""
        # Test x_coordinate out of range
        planet_data = self.valid_planet_data.copy()
        planet_data["x_coordinate"] = 32  # Should be 0-31
        planet = Planet(**planet_data)
        errors = planet.validate()
        self.assertIn("X coordinate must be between 0 and 31.", errors)
        
        # Test y_coordinate out of range
        planet_data = self.valid_planet_data.copy()
        planet_data["y_coordinate"] = -1  # Should be 0-40
        planet = Planet(**planet_data)
        errors = planet.validate()
        self.assertIn("Y coordinate must be between 0 and 40.", errors)

    def test_planet_validation_uwp_edge_cases(self):
        """Test planet validation with edge case UWPs."""
        # Test valid UWP without trade code
        planet_data = self.valid_planet_data.copy()
        planet_data["uwp"] = "A123456"  # Valid without trade code
        planet = Planet(**planet_data)
        errors = planet.validate()
        self.assertEqual(len(errors), 0, f"Expected no validation errors, but got: {errors}")
        
        # Test valid UWP with trade code
        planet_data["uwp"] = "A123456-7"  # Valid with trade code
        planet = Planet(**planet_data)
        errors = planet.validate()
        self.assertEqual(len(errors), 0, f"Expected no validation errors, but got: {errors}")
        
        # Test invalid UWP format
        planet_data["uwp"] = "A12345"  # Too short
        planet = Planet(**planet_data)
        errors = planet.validate()
        self.assertIn("Invalid UWP format. Expected format: X123456-7 or X123456-", errors)

    def test_planet_str_representation(self):
        """Test the string representation of a planet."""
        planet = Planet(**self.valid_planet_data)
        self.assertIn("Terra", str(planet))
        self.assertIn("A123456-7", str(planet))
    
    def test_from_dict_and_to_dict(self):
        """Test the from_dict and to_dict methods."""
        # Test with all fields
        planet1 = Planet(**self.valid_planet_data)
        planet_dict = planet1.to_dict()
        planet2 = Planet.from_dict(planet_dict)
        
        # Verify all fields are preserved
        for field in self.valid_planet_data:
            self.assertEqual(getattr(planet1, field), getattr(planet2, field))
        
        # Test with extra fields that should be ignored
        test_data = self.valid_planet_data.copy()
        test_data["extra_field"] = "This should be ignored"
        planet3 = Planet.from_dict(test_data)
        self.assertFalse(hasattr(planet3, "extra_field"))

if __name__ == "__main__":
    unittest.main()
