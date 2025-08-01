-- Migration: Add planet_maps table for storing planet map images
-- This table stores planet maps downloaded from TravellerWorlds.com API

-- Create the planet_maps table if it doesn't exist
CREATE TABLE IF NOT EXISTS planet_maps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planet_id INTEGER NOT NULL,
    map_data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on planet_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_planet_maps_planet_id ON planet_maps(planet_id);

-- Log the migration
INSERT INTO migrations (name, applied_at) 
VALUES ('1753858880_add_planet_maps_table.sql', CURRENT_TIMESTAMP);
