-- Add the subsectors table
CREATE TABLE subsectors (
    subsector_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    designation CHAR(1) NOT NULL,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id) ON DELETE CASCADE
);

-- Add the allegiances table
CREATE TABLE allegiances (
    allegiance_code TEXT PRIMARY KEY,
    allegiance_name TEXT NOT NULL
);

-- Add columns to planets (handled via script validation)
ALTER TABLE planets ADD COLUMN subsector_id INTEGER;
ALTER TABLE planets ADD COLUMN trade_codes TEXT;
ALTER TABLE planets ADD COLUMN travel_zone TEXT;
ALTER TABLE planets ADD COLUMN importance TEXT;
ALTER TABLE planets ADD COLUMN economic TEXT;
ALTER TABLE planets ADD COLUMN pbg TEXT;

-- Add foreign key constraints for new columns
PRAGMA foreign_keys=off;
CREATE TABLE planets_new AS
SELECT 
    planet_id, name, sector_id, NULL AS subsector_id, x_coordinate, y_coordinate, UPP,
    description, image_path, starport, size, atmosphere, hydrographics, 
    population, government, law_level, tech_level, 
    allegiance, stellar, gas_giant, bases, NULL AS trade_codes, 
    NULL AS travel_zone, NULL AS importance, NULL AS economic, hex, NULL AS pbg
FROM planets;

DROP TABLE planets;
ALTER TABLE planets_new RENAME TO planets;

CREATE INDEX idx_planets_sector ON planets(sector_id);
CREATE INDEX idx_planets_subsector ON planets(subsector_id);

PRAGMA foreign_keys=on;

-- Record the migration
INSERT INTO migrations (migration_name) VALUES ('2025-03-12_add_subsectors_allegiances');
