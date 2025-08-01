-- Schema for storing missions and their particulars

-- Sectors table
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subsectors table
CREATE TABLE IF NOT EXISTS subsectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sector_id) REFERENCES sectors(id),
    UNIQUE(sector_id, name)
);

-- Planets/worlds table
CREATE TABLE IF NOT EXISTS worlds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subsector_id INTEGER,
    name TEXT NOT NULL,
    uwp TEXT NOT NULL,
    remarks TEXT,
    zone TEXT,
    bases TEXT,
    stellar TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subsector_id) REFERENCES subsectors(id),
    UNIQUE(subsector_id, name)
);

-- Missions table
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    scenario_type TEXT NOT NULL,
    description TEXT NOT NULL,
    map_description TEXT,
    gpt_enhanced BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (world_id) REFERENCES worlds(id)
);

-- Mission details table
CREATE TABLE IF NOT EXISTS mission_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    detail_type TEXT NOT NULL,
    detail_name TEXT NOT NULL,
    detail_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id),
    UNIQUE(mission_id, detail_type)
);

-- Mission references table (for tracking which tables were used)
CREATE TABLE IF NOT EXISTS mission_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    phase TEXT NOT NULL,
    table_id TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id)
);

-- Mission particulars table (for storing ChatGPT generated content)
CREATE TABLE IF NOT EXISTS mission_particulars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    particular_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(id),
    UNIQUE(mission_id, particular_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_worlds_subsector ON worlds(subsector_id);
CREATE INDEX IF NOT EXISTS idx_missions_world ON missions(world_id);
CREATE INDEX IF NOT EXISTS idx_mission_details_mission ON mission_details(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_references_mission ON mission_references(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_particulars_mission ON mission_particulars(mission_id);
