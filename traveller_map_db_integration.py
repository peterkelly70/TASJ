#!/usr/bin/env python3
"""
Traveller Map Database Integration

This script integrates data from the Traveller Map API into the application's database.
It fetches sector and system data from the API and stores it in the database.
"""

import os
import sys
import json
import sqlite3
import logging
from PyQt6.QtWidgets import QApplication
from model.traveller_map_api_fixed_v2 import TravellerMapAPI
from model.traveller_map_data_mapper import TravellerMapDataMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "database/traveller_campaign.db"

class TravellerMapDBIntegration:
    """
    Integrates Traveller Map API data into the application's database.
    """
    
    def __init__(self, db_path=DB_PATH):
        """
        Initialize the database integration.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Create API client and data mapper
        self.api = TravellerMapAPI()
        self.mapper = TravellerMapDataMapper(self.api)
        
    def connect_db(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
            
    def close_db(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def commit(self):
        """Commit changes to the database."""
        if self.conn:
            self.conn.commit()
            logger.info("Changes committed to database")
            
    def store_sector(self, sector_name, milieu=None):
        """
        Store a sector and its systems in the database.
        
        Args:
            sector_name: Name of the sector to store
            milieu: Optional milieu code
            
        Returns:
            sector_id: ID of the stored sector
        """
        logger.info(f"Storing sector {sector_name} in database")
        
        # Fetch and map sector data
        mapped_sector = self.mapper.fetch_and_map_sector(sector_name, milieu)
        if not mapped_sector:
            logger.error(f"Failed to fetch sector data for {sector_name}")
            return None
            
        # Connect to database
        self.connect_db()
        
        try:
            # Check if sector already exists
            self.cursor.execute(
                "SELECT sector_id FROM sectors WHERE name = ?",
                (sector_name,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Update existing sector
                sector_id = result[0]
                logger.info(f"Updating existing sector: {sector_name} (ID: {sector_id})")
                
                self.cursor.execute(
                    """
                    UPDATE sectors SET 
                    x_coordinate = ?, 
                    y_coordinate = ?, 
                    image_path = ?,
                    abbreviation = ?,
                    milieu = ?
                    WHERE sector_id = ?
                    """,
                    (
                        mapped_sector['x'],
                        mapped_sector['y'],
                        mapped_sector['image_path'],
                        mapped_sector['abbreviation'],
                        milieu or 'M1105',
                        sector_id
                    )
                )
            else:
                # Insert new sector
                logger.info(f"Inserting new sector: {sector_name}")
                
                self.cursor.execute(
                    """
                    INSERT INTO sectors 
                    (name, x_coordinate, y_coordinate, image_path, abbreviation, milieu)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sector_name,
                        mapped_sector['x'],
                        mapped_sector['y'],
                        mapped_sector['image_path'],
                        mapped_sector['abbreviation'],
                        milieu or 'M1105'
                    )
                )
                
                # Get the new sector ID
                sector_id = self.cursor.lastrowid
                
            # Store systems for this sector
            self.store_systems(mapped_sector['systems'], sector_id)
            
            # Commit changes
            self.commit()
            
            logger.info(f"Successfully stored sector {sector_name} (ID: {sector_id})")
            return sector_id
            
        except sqlite3.Error as e:
            logger.error(f"Database error storing sector: {e}")
            return None
        finally:
            self.close_db()
            
    def store_systems(self, systems, sector_id):
        """
        Store systems in the database and link them to the sector.
        
        Args:
            systems: List of mapped system data
            sector_id: ID of the sector these systems belong to
        """
        logger.info(f"Storing {len(systems)} systems for sector ID {sector_id}")
        
        for system in systems:
            try:
                # Check if system already exists
                self.cursor.execute(
                    "SELECT system_id FROM systems WHERE name = ? AND hex = ? AND sector_id = ?",
                    (system['name'], system['hex'], sector_id)
                )
                result = self.cursor.fetchone()
                
                # Convert trade codes list to string if it exists
                trade_codes = None
                if 'trade_codes' in system and system['trade_codes']:
                    if isinstance(system['trade_codes'], list):
                        trade_codes = ' '.join(system['trade_codes'])
                    else:
                        trade_codes = str(system['trade_codes'])
                
                if result:
                    # Update existing system
                    system_id = result[0]
                    logger.info(f"Updating existing system: {system['name']} (ID: {system_id})")
                    
                    self.cursor.execute(
                        """
                        UPDATE systems SET 
                        uwp = ?, 
                        bases = ?, 
                        zone = ?, 
                        pbg = ?, 
                        allegiance_code = ?, 
                        stellar_data = ?, 
                        x = ?, 
                        y = ?, 
                        image_path = ?,
                        trade_codes = ?
                        WHERE system_id = ?
                        """,
                        (
                            system.get('uwp', ''),
                            system.get('bases', ''),
                            system.get('zone', ''),
                            system.get('pbg', ''),
                            system.get('allegiance', ''),
                            system.get('stellar', ''),
                            system.get('x', 0),
                            system.get('y', 0),
                            system.get('image_path', ''),
                            trade_codes,
                            system_id
                        )
                    )
                else:
                    # Insert new system
                    logger.info(f"Inserting new system: {system['name']} ({system['hex']})")
                    
                    self.cursor.execute(
                        """
                        INSERT INTO systems 
                        (name, hex, uwp, bases, zone, pbg, allegiance_code, 
                        stellar_data, x, y, image_path, sector_id, trade_codes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            system['name'],
                            system['hex'],
                            system.get('uwp', ''),
                            system.get('bases', ''),
                            system.get('zone', ''),
                            system.get('pbg', ''),
                            system.get('allegiance', ''),
                            system.get('stellar', ''),
                            system.get('x', 0),
                            system.get('y', 0),
                            system.get('image_path', ''),
                            sector_id,
                            trade_codes
                        )
                    )
                    
                    # Get the new system ID
                    system_id = self.cursor.lastrowid
                    
                    # Link system to sector in sector_has_system table
                    self.cursor.execute(
                        """
                        INSERT OR IGNORE INTO sector_has_system 
                        (sector_id, system_id)
                        VALUES (?, ?)
                        """,
                        (sector_id, system_id)
                    )
                    
            except sqlite3.Error as e:
                logger.error(f"Database error storing system {system['name']}: {e}")
                
    def store_system_with_image(self, sector_name, hex_code, milieu=None):
        """
        Store a specific system with its image in the database.
        
        Args:
            sector_name: Name of the sector
            hex_code: Hex code of the system
            milieu: Optional milieu code
            
        Returns:
            system_id: ID of the stored system
        """
        logger.info(f"Storing system {sector_name} {hex_code} in database")
        
        try:
            # Fetch and map system data
            mapped_system = self.mapper.fetch_and_map_system(sector_name, hex_code, milieu)
            if not mapped_system:
                logger.error(f"Failed to fetch system data for {sector_name} {hex_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching system data: {e}")
            return None
            
        # Connect to database
        self.connect_db()
        
        try:
            # Get sector ID
            self.cursor.execute(
                "SELECT sector_id FROM sectors WHERE name = ?",
                (sector_name,)
            )
            result = self.cursor.fetchone()
            
            if not result:
                logger.warning(f"Sector {sector_name} not found in database, creating it")
                sector_id = self.store_sector(sector_name, milieu)
                if not sector_id:
                    logger.error(f"Failed to create sector {sector_name}")
                    return None
            else:
                sector_id = result[0]
                
            # Check if system already exists
            self.cursor.execute(
                "SELECT system_id FROM systems WHERE name = ? AND hex = ? AND sector_id = ?",
                (mapped_system['name'], mapped_system['hex'], sector_id)
            )
            result = self.cursor.fetchone()
            
            # Convert trade codes list to string if it exists
            trade_codes = None
            if 'trade_codes' in mapped_system and mapped_system['trade_codes']:
                if isinstance(mapped_system['trade_codes'], list):
                    trade_codes = ' '.join(mapped_system['trade_codes'])
                else:
                    trade_codes = str(mapped_system['trade_codes'])
            
            if result:
                # Update existing system
                system_id = result[0]
                logger.info(f"Updating existing system: {mapped_system['name']} (ID: {system_id})")
                
                self.cursor.execute(
                    """
                    UPDATE systems SET 
                    uwp = ?, 
                    bases = ?, 
                    zone = ?, 
                    pbg = ?, 
                    allegiance_code = ?, 
                    stellar_data = ?, 
                    x = ?, 
                    y = ?, 
                    image_path = ?,
                    trade_codes = ?
                    WHERE system_id = ?
                    """,
                    (
                        mapped_system.get('uwp', ''),
                        mapped_system.get('bases', ''),
                        mapped_system.get('zone', ''),
                        mapped_system.get('pbg', ''),
                        mapped_system.get('allegiance', ''),
                        mapped_system.get('stellar', ''),
                        mapped_system.get('x', 0),
                        mapped_system.get('y', 0),
                        mapped_system.get('image_path', ''),
                        trade_codes,
                        system_id
                    )
                )
            else:
                # Insert new system
                logger.info(f"Inserting new system: {mapped_system['name']} ({mapped_system['hex']})")
                
                self.cursor.execute(
                    """
                    INSERT INTO systems 
                    (name, hex, uwp, bases, zone, pbg, allegiance_code, 
                    stellar_data, x, y, image_path, sector_id, trade_codes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mapped_system['name'],
                        mapped_system['hex'],
                        mapped_system.get('uwp', ''),
                        mapped_system.get('bases', ''),
                        mapped_system.get('zone', ''),
                        mapped_system.get('pbg', ''),
                        mapped_system.get('allegiance', ''),
                        mapped_system.get('stellar', ''),
                        mapped_system.get('x', 0),
                        mapped_system.get('y', 0),
                        mapped_system.get('image_path', ''),
                        sector_id,
                        trade_codes
                    )
                )
                
                # Get the new system ID
                system_id = self.cursor.lastrowid
                
                # Link system to sector in sector_has_system table
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO sector_has_system 
                    (sector_id, system_id)
                    VALUES (?, ?)
                    """,
                    (sector_id, system_id)
                )
                
            # Commit changes
            self.commit()
            
            logger.info(f"Successfully stored system {mapped_system['name']} (ID: {system_id})")
            return system_id
            
        except sqlite3.Error as e:
            logger.error(f"Database error storing system: {e}")
            return None
        finally:
            self.close_db()
            
    def search_and_store(self, query):
        """
        Search for systems and store the results in the database.
        
        Args:
            query: Search query string
            
        Returns:
            List of system IDs that were stored
        """
        logger.info("Searching and storing results for query: {}".format(query))
        
        try:
            # Search for systems
            search_results = self.mapper.search_and_map_results(query)
            if not search_results:
                logger.error("No search results found for {}".format(query))
                return []
        except Exception as e:
            logger.error("Error searching for {}: {}".format(query, e))
            return []
        
        # Store each system
        system_ids = []
        for result in search_results:
            sector = result.get('sector')
            hex_code = result.get('hex')
            
            if not sector or not hex_code:
                logger.warning("Missing sector or hex in search result: {}".format(result))
                continue
                
            # Store the system
            system_id = self.store_system_with_image(sector, hex_code)
            if system_id:
                system_ids.append(system_id)
        
        return system_ids


def main():
    """Main entry point for the database integration script."""
    print("=== TRAVELLER MAP DATABASE INTEGRATION ===")
    
    # Need QApplication for QPixmap
    _ = QApplication.instance() or QApplication(sys.argv)  # Keep reference to prevent garbage collection
    
    # Create database integration
    db_integration = TravellerMapDBIntegration()
    
    # Example 1: Store a sector
    print("\n1. Storing sector data...")
    sector_name = "Spinward Marches"
    sector_id = db_integration.store_sector(sector_name)
    
    if sector_id:
        print("✓ Successfully stored sector: {} (ID: {})".format(sector_name, sector_id))
    else:
        print("✗ Failed to store sector {}".format(sector_name))
    
    # Example 2: Store a specific system with image
    print("\n2. Storing system data...")
    system_hex = "1910"  # Regina
    system_id = db_integration.store_system_with_image(sector_name, system_hex)
    
    if system_id:
        print("✓ Successfully stored system: Regina (ID: {})".format(system_id))
    else:
        print("✗ Failed to store system Regina")
    
    # Example 3: Search and store results
    print("\n3. Searching and storing results...")
    search_term = "Regina"
    system_ids = db_integration.search_and_store(search_term)
    
    if system_ids:
        print("✓ Successfully stored {} systems from search results".format(len(system_ids)))
        print("  - System IDs: {}".format(system_ids))
    else:
        print("✗ No systems stored from search results")
    
    print("\n=== DATABASE INTEGRATION COMPLETED ===")

if __name__ == "__main__":
    main()
