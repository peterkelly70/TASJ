from typing import List, Optional, Dict, Any
from .planet import Planet
import logging

logger = logging.getLogger(__name__)

class PlanetDB:
    """
    Database interface for planet operations.
    Handles all database interactions for planet-related functionality.
    """
    
    def __init__(self, db_instance):
        """
        Initialize the PlanetDB with a valid database instance.
        
        Args:
            db_instance: An instance of TravellerDatabase with methods like
                       create_record(), read_records(), update_record(), delete_record()
        """
        self.db = db_instance
    
    def create_planet(self, planet: Planet) -> Optional[int]:
        """
        Create a new planet record in the database.
        
        Args:
            planet: Planet object containing planet data
            
        Returns:
            int: The ID of the newly created planet, or None if creation failed
        """
        try:
            # Validate planet data
            validation_errors = planet.validate()
            if validation_errors:
                logger.error(f"Validation failed: {', '.join(validation_errors)}")
                return None
                
            # Convert Planet object to dictionary for database operations
            planet_data = planet.to_dict()
            
            # Remove None values and the planet_id (for new records)
            planet_data = {k: v for k, v in planet_data.items() 
                          if v is not None and k != 'planet_id'}
            
            # Create the record
            planet_id = self.db.create_record("planets", planet_data)
            if planet_id:
                logger.info(f"Created planet {planet.name} with ID {planet_id}")
                return planet_id
            return None
            
        except Exception as e:
            logger.error(f"Error creating planet: {str(e)}", exc_info=True)
            return None
    
    def get_planet(self, planet_id: int) -> Optional[Planet]:
        """
        Retrieve a planet by its ID.
        
        Args:
            planet_id: The ID of the planet to retrieve
            
        Returns:
            Planet: Planet object if found, None otherwise
        """
        try:
            records = self.db.read_records("planets", {"planet_id": planet_id}, limit=1)
            if records:
                return Planet.from_dict(records[0])
            return None
        except Exception as e:
            logger.error(f"Error retrieving planet {planet_id}: {str(e)}")
            return None
    
    def get_planet_by_name(self, name: str, sector_id: Optional[int] = None) -> Optional[Planet]:
        """
        Retrieve a planet by its name, optionally filtered by sector.
        
        Args:
            name: The name of the planet to find
            sector_id: Optional sector ID to narrow the search
            
        Returns:
            Planet: The first matching planet, or None if not found
        """
        try:
            conditions = {"name": name}
            if sector_id is not None:
                conditions["sector_id"] = sector_id
                
            records = self.db.read_records("planets", conditions, limit=1)
            if records:
                return Planet.from_dict(records[0])
            return None
        except Exception as e:
            logger.error(f"Error finding planet by name {name}: {str(e)}")
            return None
    
    def get_planets_by_sector(self, sector_id: int) -> List[Planet]:
        """
        Retrieve all planets in a specific sector.
        
        Args:
            sector_id: The ID of the sector
            
        Returns:
            List[Planet]: List of planets in the sector
        """
        try:
            records = self.db.read_records("planets", {"sector_id": sector_id})
            return [Planet.from_dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error retrieving planets for sector {sector_id}: {str(e)}")
            return []
    
    def update_planet(self, planet: Planet) -> bool:
        """
        Update an existing planet in the database.
        
        Args:
            planet: Planet object with updated data (must have planet_id set)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not planet.planet_id:
            logger.error("Cannot update planet: No planet_id provided")
            return False
            
        try:
            # Validate planet data
            validation_errors = planet.validate()
            if validation_errors:
                logger.error(f"Validation failed: {', '.join(validation_errors)}")
                return False
                
            # Convert Planet object to dictionary for database operations
            planet_data = planet.to_dict()
            
            # Remove None values and the planet_id (we don't update the ID)
            planet_data = {k: v for k, v in planet_data.items() 
                          if v is not None and k != 'planet_id'}
            
            # Update the record
            success = self.db.update_record(
                "planets", 
                {"planet_id": planet.planet_id}, 
                planet_data
            )
            
            if success:
                logger.info(f"Updated planet {planet.planet_id} ({planet.name})")
            else:
                logger.warning(f"No changes made to planet {planet.planet_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating planet {planet.planet_id}: {str(e)}")
            return False
    
    def delete_planet(self, planet_id: int) -> bool:
        """
        Delete a planet from the database.
        
        Args:
            planet_id: The ID of the planet to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            success = self.db.delete_record("planets", {"planet_id": planet_id})
            if success:
                logger.info(f"Deleted planet with ID {planet_id}")
            else:
                logger.warning(f"No planet found with ID {planet_id} to delete")
            return success
        except Exception as e:
            logger.error(f"Error deleting planet {planet_id}: {str(e)}")
            return False
    
    def search_planets(self, search_terms: Dict[str, Any], limit: int = 100) -> List[Planet]:
        """
        Search for planets matching the given criteria.
        
        Args:
            search_terms: Dictionary of field names and values to search for
            limit: Maximum number of results to return
            
        Returns:
            List[Planet]: List of matching planets
        """
        try:
            records = self.db.read_records("planets", search_terms, limit=limit)
            return [Planet.from_dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error searching planets: {str(e)}")
            return []

    def update_planet(self, planet_name, sector_id, data):
        """
        Updates an existing planet record (identified by 'name' and optionally 'sector_id')
        with the provided data dictionary.
        Uses 'UWP' as the field for the world profile.
        Returns True if the update was successful, False otherwise.
        """
        conditions = {"name": planet_name}
        if sector_id is not None:
            conditions["sector_id"] = sector_id
        result = self.db.update_record("planets", data, conditions)
        if result == 1:
            print(f"Planet '{planet_name}' updated successfully.")
            return True
        else:
            print(f"Failed to update planet '{planet_name}'.")
            return False

    def upsert_planet(self, data):
        """
        Performs an upsert (update if exists, insert if not) for a planet record.
        Uses 'name' and 'sector_id' as unique identifiers.
        Returns True if the operation is successful, False otherwise.
        """
        planet = self.get_planet_by_name(data.get("name"), data.get("sector_id"))
        if planet:
            return self.update_planet(data.get("name"), data.get("sector_id"), data)
        else:
            return self.create_planet(data)
