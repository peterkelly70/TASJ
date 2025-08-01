"""
Mission Database Manager for Traveller RPG campaigns.

This module handles database operations for missions, including storing and retrieving
mission data, particulars, and associations with sectors/planets.
"""

import sqlite3
import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class MissionDBManager:
    """
    Handles database operations for missions, including storing and retrieving
    mission data, particulars, and associations with sectors/planets.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the mission database manager.
        
        Args:
            db_path: Optional path to the database file. If None, uses default path.
        """
        if db_path is None:
            self.db_path = str(Path(__file__).parent.parent / "data" / "missions.db")
        else:
            self.db_path = db_path
        
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize the database if it doesn't exist
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database with the required schema."""
        try:
            # Check if database exists and has tables
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if missions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='missions'")
            if cursor.fetchone() is None:
                logger.info(f"Initializing missions database at {self.db_path}")
                
                # Read and execute the schema SQL
                schema_path = Path(__file__).parent / "missions_schema.sql"
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Missions database schema created successfully")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error initializing missions database: {e}")
            raise
    
    def get_or_create_sector(self, sector_name: str) -> int:
        """
        Get or create a sector by name.
        
        Args:
            sector_name: The name of the sector
            
        Returns:
            The sector ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if sector exists
            cursor.execute("SELECT id FROM sectors WHERE name = ?", (sector_name,))
            result = cursor.fetchone()
            
            if result:
                sector_id = result[0]
            else:
                # Create new sector
                cursor.execute("INSERT INTO sectors (name) VALUES (?)", (sector_name,))
                sector_id = cursor.lastrowid
                conn.commit()
            
            return sector_id
        
        finally:
            conn.close()
    
    def get_or_create_subsector(self, sector_id: int, subsector_name: str) -> int:
        """
        Get or create a subsector by name within a sector.
        
        Args:
            sector_id: The ID of the parent sector
            subsector_name: The name of the subsector
            
        Returns:
            The subsector ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if subsector exists
            cursor.execute(
                "SELECT id FROM subsectors WHERE sector_id = ? AND name = ?", 
                (sector_id, subsector_name)
            )
            result = cursor.fetchone()
            
            if result:
                subsector_id = result[0]
            else:
                # Create new subsector
                cursor.execute(
                    "INSERT INTO subsectors (sector_id, name) VALUES (?, ?)",
                    (sector_id, subsector_name)
                )
                subsector_id = cursor.lastrowid
                conn.commit()
            
            return subsector_id
        
        finally:
            conn.close()
    
    def get_or_create_world(self, world_data: Dict[str, Any], subsector_id: Optional[int] = None) -> int:
        """
        Get or create a world based on its data.
        
        Args:
            world_data: Dictionary containing world information
            subsector_id: Optional subsector ID
            
        Returns:
            The world ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract world data
            name = world_data.get("name", "Unknown")
            uwp = world_data.get("UWP", "")
            remarks = world_data.get("remarks", "")
            zone = world_data.get("zone", "")
            bases = world_data.get("bases", "")
            stellar = world_data.get("stellar", "")
            
            # Check if world exists
            if subsector_id:
                cursor.execute(
                    "SELECT id FROM worlds WHERE subsector_id = ? AND name = ?", 
                    (subsector_id, name)
                )
            else:
                cursor.execute("SELECT id FROM worlds WHERE name = ? AND uwp = ?", (name, uwp))
            
            result = cursor.fetchone()
            
            if result:
                world_id = result[0]
                
                # Update world data if needed
                cursor.execute(
                    """
                    UPDATE worlds 
                    SET uwp = ?, remarks = ?, zone = ?, bases = ?, stellar = ?
                    WHERE id = ?
                    """,
                    (uwp, remarks, zone, bases, stellar, world_id)
                )
                conn.commit()
            else:
                # Create new world
                cursor.execute(
                    """
                    INSERT INTO worlds 
                    (subsector_id, name, uwp, remarks, zone, bases, stellar)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (subsector_id, name, uwp, remarks, zone, bases, stellar)
                )
                world_id = cursor.lastrowid
                conn.commit()
            
            return world_id
        
        finally:
            conn.close()
    
    def save_mission(self, mission_data: Dict[str, Any], world_id: int = None) -> int:
        """
        Save a mission to the database.
        
        Args:
            mission_data: Dictionary or Mission object containing mission information
            world_id: The ID of the world this mission is for. If None, will try to extract from mission_data
            
        Returns:
            The mission ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if mission_data is a Mission object and extract world_id if needed
            if hasattr(mission_data, 'to_dict'):
                # It's a Mission object, convert to dict
                mission_dict = mission_data.to_dict()
                
                # Extract world_id from the world data if not provided
                if world_id is None and 'world' in mission_dict:
                    world_id = mission_dict['world'].get('id')
                    
                # If still None, use a default value
                if world_id is None:
                    world_id = 1  # Default to world_id 1 (usually the first world)
                    
                # Extract other mission data from the Mission object
                title = mission_dict.get("scenario_type", {}).get("name", f"Mission on World {world_id}")
                scenario_type = mission_dict.get("scenario_type", {}).get("name", "Unknown")
                description = mission_dict.get("tech_context", "") + " " + mission_dict.get("environment", "")
                map_description = mission_dict.get("map_description", "")
                gpt_enhanced = 1 if mission_dict.get("gpt_enhanced", False) else 0
            else:
                # It's a dictionary, extract data directly
                # Extract world_id from the world data if not provided
                if world_id is None and 'world' in mission_data:
                    world_id = mission_data['world'].get('id')
                    
                # If still None, use a default value
                if world_id is None:
                    world_id = 1  # Default to world_id 1 (usually the first world)
                    
                # Extract mission data
                title = mission_data.get("title", f"Mission on World {world_id}")
                scenario_type = mission_data.get("structure", {}).get("scenario_type", {}).get("name", "Unknown")
                description = mission_data.get("description", "")
                map_description = mission_data.get("map_description", "")
                gpt_enhanced = 1 if mission_data.get("gpt_enhanced", False) else 0
            
            # Insert mission
            cursor.execute(
                """
                INSERT INTO missions 
                (world_id, title, scenario_type, description, map_description, gpt_enhanced)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (world_id, title, scenario_type, description, map_description, gpt_enhanced)
            )
            mission_id = cursor.lastrowid
            conn.commit()
            
            # Insert mission details
            details = mission_data.get("structure", {}).get("details", {})
            for detail_type, detail_info in details.items():
                cursor.execute(
                    """
                    INSERT INTO mission_details
                    (mission_id, detail_type, detail_name, detail_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        mission_id, 
                        detail_type, 
                        detail_info.get("name", "Unknown"), 
                        detail_info.get("id", "0")
                    )
                )
            
            # Insert mission references
            references = mission_data.get("structure", {}).get("references", [])
            for ref in references:
                cursor.execute(
                    """
                    INSERT INTO mission_references
                    (mission_id, phase, table_id, result)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        mission_id,
                        ref.get("phase", ""),
                        ref.get("table_id", ""),
                        ref.get("result", "")
                    )
                )
            
            conn.commit()
            return mission_id
        
        finally:
            conn.close()
    
    def save_mission_particulars(self, mission_id: int, particulars: Dict[str, str]) -> None:
        """
        Save mission particulars generated by ChatGPT.
        
        Args:
            mission_id: The ID of the mission
            particulars: Dictionary of particular_type -> content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Print debug info
            logger.info(f"Saving mission particulars for mission_id: {mission_id}")
            logger.info(f"Particulars keys: {list(particulars.keys())}")
            
            # Ensure we have a valid content field
            if 'content' not in particulars or not particulars['content']:
                logger.info("Adding default content to particulars")
                particulars['content'] = "Mission particulars not available."
            
            for particular_type, content in particulars.items():
                # Skip None values or empty strings for content field
                if particular_type == 'content' and (content is None or content == ''):
                    logger.warning(f"Skipping empty content for mission_id {mission_id}")
                    continue
                    
                # Ensure content is never NULL or empty string for any field
                if content is None or (particular_type == 'content' and content == ''):
                    logger.info(f"Setting default value for NULL/empty {particular_type}")
                    content = "Not available" if particular_type == 'content' else ""
                
                # Convert Python objects to JSON strings for SQLite storage
                if isinstance(content, (list, dict, tuple)):
                    logger.info(f"Converting {particular_type} from {type(content)} to JSON string")
                    content = json.dumps(content)
                
                # Log what we're about to save
                logger.info(f"Saving particular_type: {particular_type}, content: '{content}' (type: {type(content)})")
                
                # Final check to ensure content is a string
                if not isinstance(content, str):
                    logger.info(f"Converting {particular_type} to string: {content}")
                    content = str(content)
                
                # Check if particular exists
                cursor.execute(
                    "SELECT id FROM mission_particulars WHERE mission_id = ? AND particular_type = ?",
                    (mission_id, particular_type)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing particular
                    cursor.execute(
                        """
                        UPDATE mission_particulars
                        SET content = ?
                        WHERE mission_id = ? AND particular_type = ?
                        """,
                        (content, mission_id, particular_type)
                    )
                    logger.info(f"Updated existing {particular_type}")
                else:
                    # Insert new particular
                    try:
                        cursor.execute(
                            """
                            INSERT INTO mission_particulars
                            (mission_id, particular_type, content)
                            VALUES (?, ?, ?)
                            """,
                            (mission_id, particular_type, content)
                        )
                        logger.info(f"Inserted new {particular_type}")
                    except Exception as e:
                        logger.error(f"Error inserting {particular_type}: {e}")
                        # If we get an error, try to provide more details
                        logger.error(f"  mission_id: {mission_id}, type: {particular_type}, content: '{content}', content_type: {type(content)}")
                        raise
            
            conn.commit()
            logger.info(f"Successfully saved all particulars for mission_id: {mission_id}")
        
        except Exception as e:
            logger.error(f"Error in save_mission_particulars: {e}")
            raise
        
        finally:
            conn.close()
    
    def get_mission(self, mission_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a mission by ID.
        
        Args:
            mission_id: The ID of the mission
            
        Returns:
            Dictionary containing mission data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get mission data
            cursor.execute(
                """
                SELECT m.*, w.name as world_name, w.uwp as world_uwp
                FROM missions m
                JOIN worlds w ON m.world_id = w.id
                WHERE m.id = ?
                """,
                (mission_id,)
            )
            mission_row = cursor.fetchone()
            
            if not mission_row:
                return None
            
            mission = dict(mission_row)
            
            # Get mission details
            cursor.execute(
                "SELECT detail_type, detail_name, detail_id FROM mission_details WHERE mission_id = ?",
                (mission_id,)
            )
            details_rows = cursor.fetchall()
            
            details = {}
            for row in details_rows:
                details[row['detail_type']] = {
                    "name": row['detail_name'],
                    "id": row['detail_id']
                }
            
            mission['details'] = details
            
            # Get mission references
            cursor.execute(
                "SELECT phase, table_id, result FROM mission_references WHERE mission_id = ?",
                (mission_id,)
            )
            references_rows = cursor.fetchall()
            
            references = []
            for row in references_rows:
                references.append({
                    "phase": row['phase'],
                    "table_id": row['table_id'],
                    "result": row['result']
                })
            
            mission['references'] = references
            
            # Get mission particulars
            cursor.execute(
                "SELECT particular_type, content FROM mission_particulars WHERE mission_id = ?",
                (mission_id,)
            )
            particulars_rows = cursor.fetchall()
            
            particulars = {}
            for row in particulars_rows:
                particulars[row['particular_type']] = row['content']
            
            mission['particulars'] = particulars
            
            return mission
        
        finally:
            conn.close()
    
    def get_missions_for_world(self, world_id: int) -> List[Dict[str, Any]]:
        """
        Get all missions for a specific world.
        
        Args:
            world_id: The ID of the world
            
        Returns:
            List of mission dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get mission IDs for this world
            cursor.execute("SELECT id FROM missions WHERE world_id = ?", (world_id,))
            mission_ids = [row['id'] for row in cursor.fetchall()]
            
            # Get full mission data for each ID
            missions = []
            for mission_id in mission_ids:
                mission = self.get_mission(mission_id)
                if mission:
                    missions.append(mission)
            
            return missions
        
        finally:
            conn.close()
    
    def delete_mission(self, mission_id: int) -> bool:
        """
        Delete a mission and all its related data.
        
        Args:
            mission_id: The ID of the mission to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete mission particulars
            cursor.execute("DELETE FROM mission_particulars WHERE mission_id = ?", (mission_id,))
            
            # Delete mission references
            cursor.execute("DELETE FROM mission_references WHERE mission_id = ?", (mission_id,))
            
            # Delete mission details
            cursor.execute("DELETE FROM mission_details WHERE mission_id = ?", (mission_id,))
            
            # Delete mission
            cursor.execute("DELETE FROM missions WHERE id = ?", (mission_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"Error deleting mission {mission_id}: {e}")
            return False
        
        finally:
            conn.close()
