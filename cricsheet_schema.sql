SET search_path TO cricket, public;

CREATE TABLE IF NOT EXISTS cricsheet_matches (
    id VARCHAR(50) PRIMARY KEY, -- The cricsheet match ID
    match_date DATE,
    format VARCHAR(50), -- Test, ODI, T20I
    team1 VARCHAR(100),
    team2 VARCHAR(100),
    gender VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cricsheet_deliveries (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(50) REFERENCES cricsheet_matches(id) ON DELETE CASCADE,
    innings INT,
    over_number INT,
    ball_number INT,
    batsman_id VARCHAR(50), -- Cricinfo ID
    bowler_id VARCHAR(50), -- Cricinfo ID
    runs_scored INT,
    batsman_runs INT,
    is_wide BOOLEAN DEFAULT FALSE,
    is_no_ball BOOLEAN DEFAULT FALSE,
    is_bye BOOLEAN DEFAULT FALSE,
    is_leg_bye BOOLEAN DEFAULT FALSE,
    is_boundary BOOLEAN DEFAULT FALSE,
    dismissal_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cricsheet_del_match ON cricsheet_deliveries(match_id);
CREATE INDEX IF NOT EXISTS idx_cricsheet_del_bat ON cricsheet_deliveries(batsman_id);
CREATE INDEX IF NOT EXISTS idx_cricsheet_del_bowl ON cricsheet_deliveries(bowler_id);
