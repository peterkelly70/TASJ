from typing import List, Optional, Dict, Any
import logging
from .relationship_db import RelationshipDB

logger = logging.getLogger(__name__)

class SystemDB:
    """
    Database interface for system operations.
    Handles all database interactions for system-related functionality.
    """
    
    def __init__(self, db_instance):
        """
        Initialize the SystemDB with a valid database instance.
        
        Args:
            db_instance: An instance of TravellerDatabase with methods like
                       create_record(), read_records(), update_record(), delete_record()
        """
        self.db = db_instance
    
    def get_system_by_hex(self, hex_coord: str, sector_id: int) -> Optional[Dict]:
        """
        Retrieves the system record for the given hex coordinate and sector ID.
        Returns the first matching record (as a dict) or None if not found.
        
        Args:
            hex_coord: The hex coordinate of the system
            sector_id: The ID of the sector the system belongs to
            
        Returns:
            dict: System data if found, None otherwise
        """
        conditions = {"hex": hex_coord, "sector_id": sector_id}
        records = self.db.read_records("systems", conditions)
        return records[0] if records else None
    
    def create_system(self, data: Dict) -> bool:
        """
        Creates a new system record in the systems table.
        Data should be a dictionary containing at least:
            - name
            - hex
            - sector_id
            
        Returns:
            bool: True if the record was created successfully, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ["name", "hex", "sector_id"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' for system creation")
                    return False
            
            # Create the record
            result = self.db.create_record("systems", data)
            if result:
                logger.info(f"System '{data.get('name')}' created successfully.")
                return True
            else:
                logger.error(f"Failed to create system '{data.get('name')}'.")
                return False
        except Exception as e:
            logger.error(f"Error creating system: {e}")
            return False
    
    def update_system(self, hex_coord: str, sector_id: int, data: Dict) -> bool:
        """
        Updates an existing system record.
        
        Args:
            hex_coord: The hex coordinate of the system to update
            sector_id: The sector ID of the system
            data: Dictionary containing the fields to update
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            conditions = {"hex": hex_coord, "sector_id": sector_id}
            result = self.db.update_record("systems", data, conditions)
            if result == 1:
                logger.info(f"System '{data.get('name')}' updated successfully.")
                return True
            else:
                logger.warning(f"Failed to update system '{data.get('name')}'.")
                return False
        except Exception as e:
            logger.error(f"Error updating system: {e}")
            return False
    
    def upsert_system(self, data: Dict) -> bool:
        """
        Performs an upsert (update if exists, insert if not) for a system record.
        Uses 'hex' and 'sector_id' as unique identifiers.
        
        Args:
            data: Dictionary containing system data
            
        Returns:
            bool: True if the operation is successful, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ["name", "hex", "sector_id"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' for system upsert")
                    return False
            
            # Check if system exists
            existing = self.get_system_by_hex(data.get("hex"), data.get("sector_id"))
            if existing:
                return self.update_system(data.get("hex"), data.get("sector_id"), data)
            else:
                return self.create_system(data)
        except Exception as e:
            logger.error(f"Error upserting system: {e}")
            return False
    
    def get_systems_by_sector(self, sector_id: int) -> List[Dict]:
        """
        Retrieves all systems for the given sector ID.
        
        Args:
            sector_id: The ID of the sector
            
        Returns:
            List[Dict]: List of system dictionaries
        """
        try:
            conditions = {"sector_id": sector_id}
            records = self.db.read_records("systems", conditions)
            return records
        except Exception as e:
            logger.error(f"Error retrieving systems for sector {sector_id}: {e}")
            return []
    
    def get_system_by_id(self, system_id: int) -> Optional[Dict]:
        """
        Retrieves a system by its ID.
        
        Args:
            system_id: The ID of the system to retrieve
            
        Returns:
            Dict: System data if found, None otherwise
        """
        try:
            conditions = {"id": system_id}
            records = self.db.read_records("systems", conditions)
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error retrieving system {system_id}: {e}")
            return None
            
    def process_system_with_planets(self, system_data: Dict, planets_data: List[Dict], planet_db, relationship_db: RelationshipDB = None) -> Dict:
        """
        Process a system and its planets, ensuring proper relationships.
        This method handles the complete system and planet relationship in the model layer.
        
        Args:
            system_data: Dictionary with system data (must contain 'name', 'hex', 'sector_id')
            planets_data: List of planet dictionaries to associate with this system
            planet_db: Instance of PlanetDB to handle planet operations
            relationship_db: Optional RelationshipDB instance for managing relationships
            
        Returns:
            Dict with summary information about the operation
        """
        result = {
            "success": False,
            "system_updated": False,
            "planets_updated": 0,
            "planets_failed": 0,
            "system_id": None,
            "error": None,
            "relationships": {
                "sector_system_added": False,
                "system_planets_added": 0,
                "system_planets_failed": 0
            }
        }
        
        try:
            # Validate system data
            required_fields = ["name", "hex", "sector_id"]
            for field in required_fields:
                if field not in system_data:
                    result["error"] = "Missing required field '{}' for system".format(field)
                    return result
            
            # Upsert the system record
            if not self.upsert_system(system_data):
                result["error"] = "Failed to upsert system {}".format(system_data.get('name'))
                return result
                
            # Get the system ID for planet foreign keys
            system_record = self.get_system_by_hex(system_data.get("hex"), system_data.get("sector_id"))
            if not system_record or "system_id" not in system_record:
                result["error"] = "Failed to retrieve system ID after upsert"
                return result
                
            system_id = system_record["system_id"]
            result["system_id"] = system_id
            result["system_updated"] = True
            
            # Create sector-system relationship if relationship_db is provided
            if relationship_db:
                sector_id = system_data.get("sector_id")
                if relationship_db.link_sector_system(sector_id, system_id):
                    result["relationships"]["sector_system_added"] = True
            
            # Process each planet and collect planet IDs for relationship table
            planet_ids = []
            
            for planet_data in planets_data:
                # Set system relationships
                planet_data["sector_id"] = system_data.get("sector_id")
                planet_data["system_name"] = system_data.get("name")
                planet_data["hex"] = system_data.get("hex")
                
                # Set default image if not present
                if "image_path" not in planet_data or not planet_data["image_path"]:
                    planet_data["image_path"] = "default_planet.png"
                
                # Upsert the planet
                if planet_db.upsert_planet(planet_data):
                    result["planets_updated"] += 1
                    
                    # Get the planet ID for relationship table
                    planet_record = planet_db.get_planet_by_name(planet_data.get("name"), planet_data.get("sector_id"))
                    if planet_record and hasattr(planet_record, 'planet_id'):
                        planet_ids.append(planet_record.planet_id)
                else:
                    result["planets_failed"] += 1
            
            # Update system-planet relationships if relationship_db is provided
            if relationship_db and planet_ids:
                rel_result = relationship_db.update_system_planets(system_id, planet_ids)
                result["relationships"]["system_planets_added"] = rel_result.get("added", 0)
                result["relationships"]["system_planets_failed"] = rel_result.get("errors", 0)
            
            result["success"] = True
            return result
            
        except Exception as e:
            result["error"] = str(e)
            logger.error("Error processing system with planets: {}".format(e))
            return result
