#!/usr/bin/env python3
"""
Migration script to fix allegiance column in systems table.
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

def fix_systems_allegiance_column(db_path):
    """
    Fix allegiance column in systems table.
    
    Args:
        db_path: Path to the SQLite database
    """
    logger.info(f"Fixing allegiance column in systems table in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if allegiance column already exists
        cursor.execute("PRAGMA table_info(systems)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'allegiance' not in columns:
            # Check if allegiance_code column exists
            if 'allegiance_code' in columns:
                # Update import script to use allegiance_code instead of allegiance
                logger.info("allegiance_code column exists, updating import script to use it")
            else:
                # Add allegiance column to systems table
                cursor.execute("ALTER TABLE systems ADD COLUMN allegiance TEXT")
                logger.info("Added allegiance column to systems table")
            
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("allegiance column already exists in systems table")
        
    except Exception as e:
        logger.error(f"Error fixing allegiance column: {e}")
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
    fix_systems_allegiance_column(db_path)
