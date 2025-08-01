#!/usr/bin/env python3
"""
Migration script to add sector_id column to systems table.
"""

import os
import sys
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def add_sector_id_to_systems(db_path):
    """
    Add sector_id column to systems table.
    
    Args:
        db_path: Path to the SQLite database
    """
    logger.info(f"Adding sector_id column to systems table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if sector_id column already exists
        cursor.execute("PRAGMA table_info(systems)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sector_id' not in columns:
            # Add sector_id column to systems table
            cursor.execute("ALTER TABLE systems ADD COLUMN sector_id INTEGER")
            logger.info("Added sector_id column to systems table")
            
            # Create index on sector_id for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_sector_id ON systems(sector_id)")
            logger.info("Created index on sector_id column")
            
            # Create sector_has_system table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sector_has_system (
                    sector_id INTEGER,
                    system_id INTEGER,
                    PRIMARY KEY (sector_id, system_id),
                    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
                    FOREIGN KEY (system_id) REFERENCES systems(system_id)
                )
            """)
            logger.info("Created sector_has_system table if it didn't exist")
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector_has_system_sector_id ON sector_has_system(sector_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector_has_system_system_id ON sector_has_system(system_id)")
            logger.info("Created indexes on sector_has_system table")
            
            # Add milieu column to systems table if it doesn't exist
            if 'milieu' not in columns:
                cursor.execute("ALTER TABLE systems ADD COLUMN milieu TEXT")
                logger.info("Added milieu column to systems table")
            
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("sector_id column already exists in systems table")
        
    except Exception as e:
        logger.error(f"Error adding sector_id column: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Get database path from environment or use default
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/.env"))
    db_path = os.getenv('DATABASE_FILE_PATH', './database/traveller_campaign.db')
    
    # Ensure db_path is absolute
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path))
        
    logger.info(f"Using database path: {db_path}")
    
    # Run the migration
    add_sector_id_to_systems(db_path)
