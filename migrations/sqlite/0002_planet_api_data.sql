-- Migration: Add Traveller API columns to the planets table
-- These columns will store additional data fetched from the Traveller Map API

-- Migration: Add Traveller API data fields to the planets table
-- This migration adds columns to store individual UPP attributes (so we don't have to decode the UPP)
-- as well as additional API-specific fields.

ALTER TABLE planets ADD COLUMN starport TEXT;
ALTER TABLE planets ADD COLUMN size TEXT;
ALTER TABLE planets ADD COLUMN atmosphere TEXT;
ALTER TABLE planets ADD COLUMN hydrographics TEXT;
ALTER TABLE planets ADD COLUMN population TEXT;
ALTER TABLE planets ADD COLUMN government TEXT;
ALTER TABLE planets ADD COLUMN law_level TEXT;
ALTER TABLE planets ADD COLUMN tech_level TEXT;
ALTER TABLE planets ADD COLUMN allegiance TEXT;
ALTER TABLE planets ADD COLUMN stellar TEXT;
ALTER TABLE planets ADD COLUMN gas_giant TEXT;
ALTER TABLE planets ADD COLUMN bases TEXT;
ALTER TABLE planets ADD COLUMN trade_codes TEXT;
ALTER TABLE planets ADD COLUMN travel_code TEXT;
ALTER TABLE planets ADD COLUMN importance TEXT;
ALTER TABLE planets ADD COLUMN economic TEXT;
