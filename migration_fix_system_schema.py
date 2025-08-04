#!/usr/bin/env python3
"""
Migration to fix systems table schema - remove inappropriate planet columns
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_database import TravellerDatabase

def fix_systems_schema():
    """Fix systems table schema - systems only need basic system info"""
    print("=== MIGRATION: Fixing systems table schema ===")
    
    db = TravellerDatabase()
    
    # Get current columns
    current_columns = db.get_table_columns('systems')
    print("Current systems columns:", current_columns)
    
    # Systems table should only have basic system info
    # The main world's details go in planets table
    required_system_columns = [
        'system_id', 'name', 'hex', 'uwp', 'bases', 'zone', 
        'pbg', 'allegiance_code', 'stellar_data', 'x', 'y', 
        'description', 'image_path', 'sector_id', 'milieu'
    ]
    
    # Create new systems table with correct schema
    cursor = db.conn.cursor()
    
    # Create backup of existing data
    cursor.execute("SELECT * FROM systems")
    existing_data = cursor.fetchall()
    
    # Drop and recreate systems table with correct schema
    cursor.execute("DROP TABLE IF EXISTS systems_new")
    cursor.execute("""
        CREATE TABLE systems (
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
            FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
        )
    """)
    
    # Insert back only the system-level data
    if existing_data:
        # Get column mapping for existing data
        old_columns = db.get_table_columns('systems')
        column_map = {col: i for i, col in enumerate(old_columns)}
        
        for row in existing_data:
            # Only keep system-level columns
            system_data = {
                'name': row[column_map.get('name', 1)],
                'hex': row[column_map.get('hex', 2)],
                'uwp': row[column_map.get('uwp', 3)],
                'bases': row[column_map.get('bases', 4)],
                'zone': row[column_map.get('zone', 5)],
                'pbg': row[column_map.get('pbg', 6)],
                'allegiance_code': row[column_map.get('allegiance_code', 7)],
                'stellar_data': row[column_map.get('stellar_data', 8)],
                'x': row[column_map.get('x', 9)],
                'y': row[column_map.get('y', 10)],
                'description': row[column_map.get('description', 11)],
                'image_path': row[column_map.get('image_path', 12)],
                'sector_id': row[column_map.get('sector_id', 13)],
                'milieu': row[column_map.get('milieu', 14)]
            }
            
            # Filter out None values
            system_data = {k: v for k, v in system_data.items() if v is not None}
            
            cursor.execute("""
                INSERT INTO systems_new (name, hex, uwp, bases, zone, pbg, 
                allegiance_code, stellar_data, x, y, description, image_path, sector_id, milieu)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                system_data.get('name', ''),
                system_data.get('hex', ''),
                system_data.get('uwp', ''),
                system_data.get('bases', ''),
                system_data.get('zone', ''),
                system_data.get('pbg', ''),
                system_data.get('allegiance_code', ''),
                system_data.get('stellar_data', ''),
                system_data.get('x', 0),
                system_data.get('y', 0),
                system_data.get('description', ''),
                system_data.get('image_path', ''),
                system_data.get('sector_id', 1),
                system_data.get('milieu', 'M1105')
            ])
    
    # Replace old table with new one
    cursor.execute("DROP TABLE systems")
    cursor.execute("ALTER TABLE systems_new RENAME TO systems")
    
    db.conn.commit()
    
    # Verify updated schema
    updated_columns = db.get_table_columns('systems')
    print("Updated systems columns:", updated_columns)
    
    print("✅ Migration completed - systems table now has correct schema")

if __name__ == "__main__":
    fix_systems_schema()
