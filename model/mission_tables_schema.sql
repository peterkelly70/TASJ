-- Mission Tables Database Schema

-- Phases table
CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Tables table
CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY,
    phase_id INTEGER NOT NULL,
    table_number TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (phase_id) REFERENCES phases(id),
    UNIQUE (phase_id, table_number)
);

-- Entries table
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    table_id INTEGER NOT NULL,
    entry_number TEXT NOT NULL,
    name TEXT NOT NULL,
    reference_table TEXT,
    FOREIGN KEY (table_id) REFERENCES tables(id),
    UNIQUE (table_id, entry_number)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tables_phase_id ON tables(phase_id);
CREATE INDEX IF NOT EXISTS idx_entries_table_id ON entries(table_id);
CREATE INDEX IF NOT EXISTS idx_entries_reference_table ON entries(reference_table);
