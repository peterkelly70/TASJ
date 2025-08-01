#!/usr/bin/env python3
"""
Migration script to add stellar column to systems table.
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

def add_stellar_to_systems(db_path):
    """
    Add stellar column to systems table.
    
    Args:
        db_path: Path to the SQLite database
    """
    logger.info(f"Adding stellar column to systems table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if stellar column already exists
        cursor.execute("PRAGMA table_info(systems)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stellar' not in columns:
            # Check if stellar_data column exists (might be using a different name)
            if 'stellar_data' in columns:
                logger.info("stellar_data column exists, updating import script to use it")
                # We'll update the import script to use stellar_data instead
            else:
                # Add stellar column to systems table
                cursor.execute("ALTER TABLE systems ADD COLUMN stellar TEXT")
                logger.info("Added stellar column to systems table")
            
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("stellar column already exists in systems table")
        
    except Exception as e:
        logger.error(f"Error adding stellar column: {e}")
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
    add_stellar_to_systems(db_path)
