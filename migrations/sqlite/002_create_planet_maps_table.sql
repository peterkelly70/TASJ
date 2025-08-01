-- Create planet_maps table for storing planet map images
CREATE TABLE IF NOT EXISTS planet_maps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planet_id TEXT NOT NULL,
    planet_name TEXT NOT NULL,
    map_image BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(planet_id)
);
