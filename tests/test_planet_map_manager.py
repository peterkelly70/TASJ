import unittest
import os
import tempfile
import sqlite3
from model.planet_map_manager import PlanetMapManager

class TestPlanetMapManager(unittest.TestCase):
    """Test cases for the PlanetMapManager class."""
    
    def setUp(self):
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create a test map manager
        self.map_manager = PlanetMapManager(self.db_path)
        
        # Sample map data (a small PNG)
        self.sample_map_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG header
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 image
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, etc.
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,  # pixel data
            0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D,  # more data
            0xB0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82                     # end of PNG
        ])
        
        # Create a test planet in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT INTO planets (id, name) VALUES (1, 'Test Planet')")
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up after tests."""
        os.unlink(self.db_path)
    
    def test_table_creation(self):
        """Test that the planet_maps table is created."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planet_maps'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "planet_maps")
    
    def test_save_and_get_map(self):
        """Test saving and retrieving a map."""
        # Save the map
        result = self.map_manager.save_map(1, self.sample_map_data)
        self.assertTrue(result)
        
        # Retrieve the map
        retrieved_data = self.map_manager.get_map(1)
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data, self.sample_map_data)
    
    def test_update_map(self):
        """Test updating an existing map."""
        # Save the initial map
        self.map_manager.save_map(1, self.sample_map_data)
        
        # Create a different map data
        updated_map_data = bytes([0x01, 0x02, 0x03, 0x04])
        
        # Update the map
        result = self.map_manager.save_map(1, updated_map_data)
        self.assertTrue(result)
        
        # Retrieve the updated map
        retrieved_data = self.map_manager.get_map(1)
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data, updated_map_data)
    
    def test_get_nonexistent_map(self):
        """Test retrieving a map that doesn't exist."""
        retrieved_data = self.map_manager.get_map(999)
        self.assertIsNone(retrieved_data)
    
    def test_delete_map(self):
        """Test deleting a map."""
        # Save a map
        self.map_manager.save_map(1, self.sample_map_data)
        
        # Delete the map
        result = self.map_manager.delete_map(1)
        self.assertTrue(result)
        
        # Try to retrieve the deleted map
        retrieved_data = self.map_manager.get_map(1)
        self.assertIsNone(retrieved_data)
    
    def test_delete_nonexistent_map(self):
        """Test deleting a map that doesn't exist."""
        result = self.map_manager.delete_map(999)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
