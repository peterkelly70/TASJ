"""
Database interface for relationship tables.
Handles all database interactions for relationship tables like sector_has_system and system_has_planet.
"""

from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class RelationshipDB:
    """
    Database interface for relationship tables.
    Handles join tables between entities like sectors, systems, and planets.
    """
    
    def __init__(self, db_instance):
        """
        Initialize the RelationshipDB with a valid database instance.
        
        Args:
            db_instance: An instance of TravellerDatabase with methods like
                       create_record(), read_records(), update_record(), delete_record()
        """
        self.db = db_instance
    
    def link_sector_system(self, sector_id: int, system_id: int) -> bool:
        """
        Create a relationship between a sector and a system in the sector_has_system table.
        
        Args:
            sector_id: The ID of the sector
            system_id: The ID of the system
            
        Returns:
            bool: True if the relationship was created successfully, False otherwise
        """
        try:
            # Check if the relationship already exists
            existing = self.db.read_records(
                "sector_has_system", 
                {"sector_id": sector_id, "system_id": system_id},
                limit=1
            )
            
            if existing:
                # Relationship already exists
                return True
                
            # Create the relationship
            data = {
                "sector_id": sector_id,
                "system_id": system_id
            }
            
            result = self.db.create_record("sector_has_system", data)
            if result:
                logger.info(f"Linked sector {sector_id} with system {system_id}")
                return True
            else:
                logger.error(f"Failed to link sector {sector_id} with system {system_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error linking sector and system: {e}")
            return False
    
    def link_system_planet(self, system_id: int, planet_id: int) -> bool:
        """
        Create a relationship between a system and a planet in the system_has_planet table.
        
        Args:
            system_id: The ID of the system
            planet_id: The ID of the planet
            
        Returns:
            bool: True if the relationship was created successfully, False otherwise
        """
        try:
            # Check if the relationship already exists
            existing = self.db.read_records(
                "system_has_planet", 
                {"system_id": system_id, "planet_id": planet_id},
                limit=1
            )
            
            if existing:
                # Relationship already exists
                return True
                
            # Create the relationship
            data = {
                "system_id": system_id,
                "planet_id": planet_id
            }
            
            result = self.db.create_record("system_has_planet", data)
            if result:
                logger.info(f"Linked system {system_id} with planet {planet_id}")
                return True
            else:
                logger.error(f"Failed to link system {system_id} with planet {planet_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error linking system and planet: {e}")
            return False
    
    def get_systems_for_sector(self, sector_id: int) -> List[int]:
        """
        Get all system IDs linked to a specific sector.
        
        Args:
            sector_id: The ID of the sector
            
        Returns:
            List[int]: List of system IDs linked to the sector
        """
        try:
            records = self.db.read_records("sector_has_system", {"sector_id": sector_id})
            return [record["system_id"] for record in records if "system_id" in record]
        except Exception as e:
            logger.error(f"Error getting systems for sector {sector_id}: {e}")
            return []
    
    def get_planets_for_system(self, system_id: int) -> List[int]:
        """
        Get all planet IDs linked to a specific system.
        
        Args:
            system_id: The ID of the system
            
        Returns:
            List[int]: List of planet IDs linked to the system
        """
        try:
            records = self.db.read_records("system_has_planet", {"system_id": system_id})
            return [record["planet_id"] for record in records if "planet_id" in record]
        except Exception as e:
            logger.error(f"Error getting planets for system {system_id}: {e}")
            return []
    
    def update_sector_systems(self, sector_id: int, system_ids: List[int]) -> Dict[str, Any]:
        """
        Update the relationships between a sector and its systems.
        This will add new relationships and remove old ones to match the provided list.
        
        Args:
            sector_id: The ID of the sector
            system_ids: List of system IDs that should be linked to this sector
            
        Returns:
            Dict: Summary of operations performed
        """
        result = {
            "success": False,
            "added": 0,
            "removed": 0,
            "unchanged": 0,
            "errors": 0
        }
        
        try:
            # Get current relationships
            current_system_ids = self.get_systems_for_sector(sector_id)
            
            # Systems to add (in new list but not in current)
            systems_to_add = [sid for sid in system_ids if sid not in current_system_ids]
            
            # Systems to remove (in current but not in new list)
            systems_to_remove = [sid for sid in current_system_ids if sid not in system_ids]
            
            # Add new relationships
            for system_id in systems_to_add:
                if self.link_sector_system(sector_id, system_id):
                    result["added"] += 1
                else:
                    result["errors"] += 1
            
            # Remove old relationships
            for system_id in systems_to_remove:
                try:
                    self.db.delete_record(
                        "sector_has_system", 
                        {"sector_id": sector_id, "system_id": system_id}
                    )
                    result["removed"] += 1
                except Exception:
                    result["errors"] += 1
            
            # Count unchanged relationships
            result["unchanged"] = len(current_system_ids) - result["removed"]
            
            # Set success flag
            result["success"] = result["errors"] == 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating sector systems: {e}")
            result["success"] = False
            return result
    
    def update_system_planets(self, system_id: int, planet_ids: List[int]) -> Dict[str, Any]:
        """
        Update the relationships between a system and its planets.
        This will add new relationships and remove old ones to match the provided list.
        
        Args:
            system_id: The ID of the system
            planet_ids: List of planet IDs that should be linked to this system
            
        Returns:
            Dict: Summary of operations performed
        """
        result = {
            "success": False,
            "added": 0,
            "removed": 0,
            "unchanged": 0,
            "errors": 0
        }
        
        try:
            # Get current relationships
            current_planet_ids = self.get_planets_for_system(system_id)
            
            # Planets to add (in new list but not in current)
            planets_to_add = [pid for pid in planet_ids if pid not in current_planet_ids]
            
            # Planets to remove (in current but not in new list)
            planets_to_remove = [pid for pid in current_planet_ids if pid not in planet_ids]
            
            # Add new relationships
            for planet_id in planets_to_add:
                if self.link_system_planet(system_id, planet_id):
                    result["added"] += 1
                else:
                    result["errors"] += 1
            
            # Remove old relationships
            for planet_id in planets_to_remove:
                try:
                    self.db.delete_record(
                        "system_has_planet", 
                        {"system_id": system_id, "planet_id": planet_id}
                    )
                    result["removed"] += 1
                except Exception:
                    result["errors"] += 1
            
            # Count unchanged relationships
            result["unchanged"] = len(current_planet_ids) - result["removed"]
            
            # Set success flag
            result["success"] = result["errors"] == 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating system planets: {e}")
            result["success"] = False
            return result
