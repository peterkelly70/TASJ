CREATE TABLE jumps (
    jump_id INTEGER PRIMARY KEY,
    start_sector TEXT,
    start_hex TEXT,
    end_sector TEXT,
    end_hex TEXT,
    jump_distance INTEGER,
    requires_fuel BOOLEAN DEFAULT 0,
    restricted_zone BOOLEAN DEFAULT 0,
    FOREIGN KEY (start_sector) REFERENCES sectors(name),
    FOREIGN KEY (end_sector) REFERENCES sectors(name)
);
