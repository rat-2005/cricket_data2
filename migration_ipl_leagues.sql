SET search_path TO cricket, public;

-- Create the leagues lookup table
CREATE TABLE IF NOT EXISTS leagues (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_tournament BOOLEAN,
    league_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the mapping table to connect events to leagues
CREATE TABLE IF NOT EXISTS event_leagues (
    event_id VARCHAR(50) REFERENCES events(id) ON DELETE CASCADE,
    league_id VARCHAR(50) REFERENCES leagues(id) ON DELETE CASCADE,
    league_type VARCHAR(50),
    PRIMARY KEY (event_id, league_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- (No existing tables need to be ALTERED, we just needed these two new tables for the IPL filter!)
