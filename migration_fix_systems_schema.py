#!/usr/bin/env python3
"""
Migration to fix systems table schema - add missing columns
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_database import TravellerDatabase

def fix_systems_schema():
    """Fix systems table schema by adding missing columns"""
    print("=== MIGRATION: Fixing systems table schema ===")
    
    db = TravellerDatabase()
    
    # Get current columns
    current_columns = db.get_table_columns('systems')
    print("Current systems columns:", current_columns)
    
    # Columns that should exist based on the population script
    required_columns = {
        'trade_codes': 'TEXT',
        'extensions': 'TEXT',
        'trade_code': 'TEXT',
        'main_world': 'TEXT',
        'worlds': 'TEXT',
        'population': 'INTEGER',
        'government': 'TEXT',
        'law_level': 'TEXT',
        'tech_level': 'TEXT',
        'port': 'TEXT',
        'gas_giant': 'TEXT',
        'planet_count': 'INTEGER',
        'world_count': 'INTEGER'
    }
    
    cursor = db.conn.cursor()
    
    columns_added = 0
    for col_name, col_type in required_columns.items():
        if col_name.lower() not in [c.lower() for c in current_columns]:
            try:
                cursor.execute(f"ALTER TABLE systems ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added {col_name} column")
                columns_added += 1
            except Exception as e:
                print(f"⚠️  Could not add {col_name}: {e}")
    
    # Also check planets table
    planet_columns = db.get_table_columns('planets')
    print("Current planets columns:", planet_columns)
    
    # Commit changes
    db.conn.commit()
    
    # Verify updated schema
    updated_columns = db.get_table_columns('systems')
    print("Updated systems columns:", updated_columns)
    
    print(f"✅ Migration completed - added {columns_added} columns")

if __name__ == "__main__":
    fix_systems_schema()
