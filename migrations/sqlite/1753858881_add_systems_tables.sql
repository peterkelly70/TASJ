-- Migration to add systems table and relationship tables
-- Created on 2025-07-31

-- Create systems table
CREATE TABLE IF NOT EXISTS systems (
    system_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    hex TEXT,
    uwp TEXT,
    bases TEXT,
    zone TEXT,
    pbg TEXT,
    allegiance_code TEXT,
    stellar_data TEXT,
    x INTEGER,
    y INTEGER,
    description TEXT,
    image_path TEXT
);

-- Create sector-system relationship table
CREATE TABLE IF NOT EXISTS sector_has_system (
    sector_id INTEGER NOT NULL,
    system_id INTEGER NOT NULL,
    PRIMARY KEY (sector_id, system_id),
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
    FOREIGN KEY (system_id) REFERENCES systems(system_id)
);

-- Create system-planet relationship table
CREATE TABLE IF NOT EXISTS system_has_planet (
    system_id INTEGER NOT NULL,
    planet_id INTEGER NOT NULL,
    PRIMARY KEY (system_id, planet_id),
    FOREIGN KEY (system_id) REFERENCES systems(system_id),
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_sector_has_system_sector_id ON sector_has_system(sector_id);
CREATE INDEX IF NOT EXISTS idx_sector_has_system_system_id ON sector_has_system(system_id);
CREATE INDEX IF NOT EXISTS idx_system_has_planet_system_id ON system_has_planet(system_id);
CREATE INDEX IF NOT EXISTS idx_system_has_planet_planet_id ON system_has_planet(planet_id);
