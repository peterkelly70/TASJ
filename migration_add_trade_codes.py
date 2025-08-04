#!/usr/bin/env python3
"""
Migration to add trade_codes column to systems table
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_database import TravellerDatabase

def add_trade_codes_column():
    """Add trade_codes column to systems table"""
    print("=== MIGRATION: Adding trade_codes column to systems table ===")
    
    db = TravellerDatabase()
    
    # Check if column already exists
    if db.column_exists('systems', 'trade_codes'):
        print("✅ trade_codes column already exists")
        return
    
    try:
        # Add trade_codes column to systems table
        cursor = db.conn.cursor()
        
        # SQLite syntax for adding column
        if db.db_type == 'sqlite':
            cursor.execute("ALTER TABLE systems ADD COLUMN trade_codes TEXT")
            print("✅ Added trade_codes column to systems table")
        elif db.db_type == 'mysql':
            cursor.execute("ALTER TABLE systems ADD COLUMN trade_codes VARCHAR(255)")
            print("✅ Added trade_codes column to systems table")
        
        db.conn.commit()
        
        # Verify the column was added
        columns = db.get_table_columns('systems')
        print("Updated systems columns:", columns)
        
        if 'trade_codes' in columns:
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed - column not found")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.conn.rollback()

if __name__ == "__main__":
    add_trade_codes_column()
