#!/usr/bin/env python3
"""
Migration to reset systems table with correct schema
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from model.traveller_database import TravellerDatabase

def reset_systems_schema():
    """Reset systems table with correct schema"""
    print("=== MIGRATION: Resetting systems table schema ===")
    
    db = TravellerDatabase()
    cursor = db.conn.cursor()
    
    # Disable foreign key constraints temporarily
    cursor.execute("PRAGMA foreign_keys=OFF")
    
    # Drop dependent tables first
    cursor.execute("DROP TABLE IF EXISTS sector_has_system")
    cursor.execute("DROP TABLE IF EXISTS planets")
    cursor.execute("DROP TABLE IF EXISTS systems")
    
    # Create systems table with correct schema
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
            trade_codes TEXT
        )
    """)
    
    # Create sector_has_system table
    cursor.execute("""
        CREATE TABLE sector_has_system (
            sector_id INTEGER,
            system_id INTEGER,
            PRIMARY KEY (sector_id, system_id),
            FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
            FOREIGN KEY (system_id) REFERENCES systems(system_id)
        )
    """)
    
    # Create planets table
    cursor.execute("""
        CREATE TABLE planets (
            planet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sector_id INTEGER,
            x_coordinate INTEGER,
            y_coordinate INTEGER,
            UPP TEXT,
            description TEXT,
            image_path TEXT,
            starport TEXT,
            size TEXT,
            atmosphere TEXT,
            hydrographics TEXT,
            population TEXT,
            government TEXT,
            law_level TEXT,
            tech_level TEXT,
            allegiance TEXT,
            stellar TEXT,
            gas_giant TEXT,
            bases TEXT,
            trade_codes TEXT,
            travel_code TEXT,
            importance TEXT,
            economic TEXT,
            hex TEXT,
            subsector_id INTEGER,
            travel_zone TEXT,
            pbg TEXT,
            UWP TEXT,
            system_name TEXT,
            system_hex TEXT,
            planet_number INTEGER,
            zone TEXT,
            allegiance_code TEXT,
            planet_type TEXT,
            radius INTEGER,
            gravity REAL,
            temperature INTEGER,
            day_length TEXT,
            year_length TEXT
        )
    """)
    
    db.conn.commit()
    
    # Verify schema
    updated_columns = db.get_table_columns('systems')
    print("Updated systems columns:", updated_columns)
    
    print("✅ Migration completed - systems table reset with correct schema")

if __name__ == "__main__":
    reset_systems_schema()
