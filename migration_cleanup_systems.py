#!/usr/bin/env python3
"""
Migration to clean up systems table - remove inappropriate planet columns
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_database import TravellerDatabase

def cleanup_systems_schema():
    """Clean up systems table by removing inappropriate columns"""
    print("=== MIGRATION: Cleaning up systems table ===")
    
    db = TravellerDatabase()
    
    # Get current columns
    current_columns = db.get_table_columns('systems')
    print("Current systems columns:", current_columns)
    
    # These are the correct system-level columns
    valid_system_columns = [
        'system_id', 'name', 'hex', 'uwp', 'bases', 'zone', 
        'pbg', 'allegiance_code', 'stellar_data', 'x', 'y', 
        'description', 'image_path', 'sector_id', 'milieu', 'trade_codes'
    ]
    
    # Identify columns to remove (planet-level fields)
    columns_to_remove = [col for col in current_columns if col not in valid_system_columns]
    
    print("Columns to remove:", columns_to_remove)
    
    # Since SQLite doesn't support DROP COLUMN easily, we'll create a new table
    cursor = db.conn.cursor()
    
    # Get existing data
    cursor.execute("SELECT * FROM systems")
    existing_data = cursor.fetchall()
    
    if existing_data:
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE systems_new (
                system_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hex TEXT NOT NULL,
                uwp TEXT,
                bases TEXT,
                zone TEXT,
                pbg TEXT,
                allegiance_code TEXT,
                stellar_data TEXT,
                x INTEGER,
                y INTEGER,
                description TEXT,
                image_path TEXT,
                sector_id INTEGER,
                milieu TEXT,
                trade_codes TEXT,
                FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
            )
        """)
        
        # Copy data with only valid columns
        for row in existing_data:
            cursor.execute("""
                INSERT INTO systems_new (name, hex, uwp, bases, zone, pbg, 
                allegiance_code, stellar_data, x, y, description, image_path, sector_id, milieu, trade_codes)
                SELECT name, hex, uwp, bases, zone, pbg, 
                allegiance_code, stellar_data, x, y, description, image_path, sector_id, milieu, trade_codes
                FROM systems WHERE system_id = ?
            """, [row[0]])
    else:
        # Just create the new table
        cursor.execute("""
            CREATE TABLE systems_new (
                system_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hex TEXT NOT NULL,
                uwp TEXT,
                bases TEXT,
                zone TEXT,
                pbg TEXT,
                allegiance_code TEXT,
                stellar_data TEXT,
                x INTEGER,
                y INTEGER,
                description TEXT,
                image_path TEXT,
                sector_id INTEGER,
                milieu TEXT,
                trade_codes TEXT,
                FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
            )
        """)
    
    # Replace old table
    cursor.execute("DROP TABLE systems")
    cursor.execute("ALTER TABLE systems_new RENAME TO systems")
    
    db.conn.commit()
    
    # Verify updated schema
    updated_columns = db.get_table_columns('systems')
    print("Updated systems columns:", updated_columns)
    
    print("✅ Migration completed - systems table now has correct schema")

if __name__ == "__main__":
    cleanup_systems_schema()
