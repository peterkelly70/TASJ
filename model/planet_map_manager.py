import logging
import sqlite3
import os
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class PlanetMapManager:
    """Manager for planet map storage and retrieval."""
    
    def __init__(self, db_path: str):
        """
        Initialize the PlanetMapManager.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the planet_maps table exists in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='planet_maps'
            """)
            
            if not cursor.fetchone():
                # Create table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE planet_maps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        planet_id INTEGER NOT NULL,
                        map_data BLOB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Created planet_maps table")
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
        finally:
            conn.close()
    
    def save_map(self, planet_id: int, map_data: bytes) -> bool:
        """
        Save a planet map to the database.
        
        Args:
            planet_id: ID of the planet
            map_data: Binary map image data
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if map already exists for this planet
            cursor.execute(
                "SELECT id FROM planet_maps WHERE planet_id = ?", 
                (planet_id,)
            )
            existing_map = cursor.fetchone()
            
            if existing_map:
                # Update existing map
                cursor.execute(
                    "UPDATE planet_maps SET map_data = ?, created_at = CURRENT_TIMESTAMP WHERE planet_id = ?",
                    (map_data, planet_id)
                )
                logger.info(f"Updated map for planet ID {planet_id}")
            else:
                # Insert new map
                cursor.execute(
                    "INSERT INTO planet_maps (planet_id, map_data) VALUES (?, ?)",
                    (planet_id, map_data)
                )
                logger.info(f"Saved new map for planet ID {planet_id}")
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving planet map: {e}")
            return False
        finally:
            conn.close()
    
    def get_map(self, planet_id: int) -> Optional[bytes]:
        """
        Get a planet map from the database.
        
        Args:
            planet_id: ID of the planet
            
        Returns:
            Binary map image data if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT map_data FROM planet_maps WHERE planet_id = ?", 
                (planet_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]  # Return binary map data
            else:
                logger.info(f"No map found for planet ID {planet_id}")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving planet map: {e}")
            return None
        finally:
            conn.close()
    
    def delete_map(self, planet_id: int) -> bool:
        """
        Delete a planet map from the database.
        
        Args:
            planet_id: ID of the planet
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM planet_maps WHERE planet_id = ?", 
                (planet_id,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted map for planet ID {planet_id}")
                return True
            else:
                logger.info(f"No map found to delete for planet ID {planet_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting planet map: {e}")
            return False
        finally:
            conn.close()
