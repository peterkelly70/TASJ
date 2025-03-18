-- 1. Add the new column `UWP` to the `planets` table
ALTER TABLE planets ADD COLUMN UWP TEXT;

-- 2. Copy the data from the `UPP` column to the new `UWP` column
UPDATE planets SET UWP = UPP;

-- 3. Create a new table without the `UPP` column (we'll keep the new `UWP` column)
CREATE TABLE planets_new (
    planet_id INTEGER PRIMARY KEY,
    name TEXT,
    sector_id INTEGER,
    x_coordinate INTEGER,
    y_coordinate INTEGER,
    UWP TEXT,  -- New column instead of UPP
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
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

-- 4. Copy data from the original `planets` table to the new `planets_new` table
INSERT INTO planets_new (planet_id, name, sector_id, x_coordinate, y_coordinate, UWP, description, image_path, starport, size, atmosphere, hydrographics, population, government, law_level, tech_level, allegiance, stellar, gas_giant, bases, trade_codes, travel_code, importance, economic, hex, subsector_id, travel_zone, pbg)
SELECT planet_id, name, sector_id, x_coordinate, y_coordinate, UPP, description, image_path, starport, size, atmosphere, hydrographics, population, government, law_level, tech_level, allegiance, stellar, gas_giant, bases, trade_codes, travel_code, importance, economic, hex, subsector_id, travel_zone, pbg
FROM planets;

-- 5. Drop the old `planets` table
DROP TABLE planets;

-- 6. Rename the new table to `planets`
ALTER TABLE planets_new RENAME TO planets;
