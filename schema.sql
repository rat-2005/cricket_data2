-- ==============================================================================
-- Enterprise Cricket Analytics Database Schema
-- Designed for PostgreSQL
-- ==============================================================================

-- Create a dedicated schema
CREATE SCHEMA IF NOT EXISTS cricket;

-- Set the search path to the new schema
SET search_path TO cricket, public;

-- ==============================================================================
-- TIER 1: Reference Data (Rarely Changes)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS venues (
    id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    capacity INTEGER,
    grass BOOLEAN,
    indoor BOOLEAN,
    address_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10),
    display_name VARCHAR(255),
    short_display_name VARCHAR(100),
    location VARCHAR(255),
    nickname VARCHAR(100),
    country_code VARCHAR(10),
    color VARCHAR(10),
    is_national BOOLEAN,
    is_active BOOLEAN,
    logo_url VARCHAR(500),
    slug VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS athletes (
    id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    country_code VARCHAR(10),
    date_of_birth TIMESTAMP WITH TIME ZONE,
    gender VARCHAR(10),
    image_url VARCHAR(500),
    batting_style VARCHAR(50),
    bowling_style VARCHAR(50),
    position VARCHAR(50),
    is_active BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 2: Match Structure
-- ==============================================================================

CREATE TABLE IF NOT EXISTS leagues (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_tournament BOOLEAN,
    league_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(50) PRIMARY KEY,
    uid VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    description TEXT,
    date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    time_valid BOOLEAN,
    api_ref VARCHAR(500),
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_leagues (
    event_id VARCHAR(50) REFERENCES events(id) ON DELETE CASCADE,
    league_id VARCHAR(50) REFERENCES leagues(id) ON DELETE CASCADE,
    league_type VARCHAR(50),
    PRIMARY KEY (event_id, league_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitions (
    id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES events(id) ON DELETE CASCADE,
    venue_id VARCHAR(50) REFERENCES venues(id) ON DELETE SET NULL,
    description VARCHAR(255),
    date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    neutral_site BOOLEAN,
    day_night BOOLEAN,
    limited_overs BOOLEAN,
    class_international_id VARCHAR(10),
    class_general_id VARCHAR(10),
    class_name VARCHAR(100),
    event_type VARCHAR(50),
    attendance INTEGER,
    play_by_play_available BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_competitions_event_type ON competitions(event_type);

CREATE TABLE IF NOT EXISTS match_status (
    competition_id VARCHAR(50) PRIMARY KEY REFERENCES competitions(id) ON DELETE CASCADE,
    state VARCHAR(50),
    detail VARCHAR(100),
    description VARCHAR(100),
    summary VARCHAR(255),
    long_summary VARCHAR(500),
    period INTEGER,
    day_number INTEGER,
    potm_athlete_id VARCHAR(50) REFERENCES athletes(id) ON DELETE SET NULL,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS match_officials (
    id SERIAL PRIMARY KEY,
    competition_id VARCHAR(50) REFERENCES competitions(id) ON DELETE CASCADE,
    display_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    country VARCHAR(100),
    role VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 3: Per-Innings
-- ==============================================================================

CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    competition_id VARCHAR(50) REFERENCES competitions(id) ON DELETE CASCADE,
    team_id VARCHAR(50) REFERENCES teams(id) ON DELETE CASCADE,
    espn_competitor_id VARCHAR(10),
    home_away VARCHAR(10),
    winner BOOLEAN,
    score_value VARCHAR(100),
    UNIQUE(competition_id, espn_competitor_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS innings (
    id SERIAL PRIMARY KEY,
    competitor_id INTEGER REFERENCES competitors(id) ON DELETE CASCADE,
    period INTEGER,
    runs INTEGER,
    wickets INTEGER,
    overs DECIMAL(5,2),
    fours INTEGER,
    sixes INTEGER,
    score VARCHAR(50),
    description VARCHAR(100),
    is_batting BOOLEAN,
    is_current BOOLEAN,
    target INTEGER,
    follow_on BOOLEAN,
    UNIQUE(competitor_id, period),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS partnerships (
    id SERIAL PRIMARY KEY,
    innings_id INTEGER REFERENCES innings(id) ON DELETE CASCADE,
    wicket_number INTEGER,
    runs INTEGER,
    balls INTEGER,
    batsman_1_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    batsman_2_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    start_overs DECIMAL(5,2),
    start_runs INTEGER,
    start_wickets INTEGER,
    end_overs DECIMAL(5,2),
    end_runs INTEGER,
    end_wickets INTEGER,
    UNIQUE(innings_id, wicket_number),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fall_of_wickets (
    id SERIAL PRIMARY KEY,
    innings_id INTEGER REFERENCES innings(id) ON DELETE CASCADE,
    wicket_number INTEGER,
    wicket_name VARCHAR(255),
    runs_scored INTEGER,
    overs DECIMAL(5,2),
    fow_type VARCHAR(100),
    UNIQUE(innings_id, wicket_number),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 4: Player Performance
-- ==============================================================================

CREATE TABLE IF NOT EXISTS player_match_performances (
    id SERIAL PRIMARY KEY,
    competitor_id INTEGER REFERENCES competitors(id) ON DELETE CASCADE,
    athlete_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    innings_number INTEGER,
    is_batting BOOLEAN,
    batting_order INTEGER,
    is_captain BOOLEAN,
    is_keeper BOOLEAN,
    runs INTEGER,
    balls_faced INTEGER,
    fours INTEGER,
    sixes INTEGER,
    strike_rate DECIMAL(7,2),
    dismissal_type VARCHAR(100),
    minutes INTEGER,
    overs_bowled DECIMAL(5,2),
    maidens INTEGER,
    runs_conceded INTEGER,
    wickets INTEGER,
    economy_rate DECIMAL(7,2),
    wides INTEGER,
    no_balls INTEGER,
    UNIQUE(competitor_id, athlete_id, innings_number),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 5: Ball-by-Ball (The Analytics Engine)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS deliveries (
    id VARCHAR(50) PRIMARY KEY,
    competition_id VARCHAR(50) REFERENCES competitions(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    bbb_timestamp BIGINT,
    date TIMESTAMP WITH TIME ZONE,
    
    period INTEGER,
    period_text VARCHAR(100),
    over_number INTEGER,
    ball_in_over INTEGER,
    overs_actual DECIMAL(5,2),
    
    batsman_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    non_striker_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    bowler_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    other_bowler_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    batting_team_id VARCHAR(50) REFERENCES teams(id) ON DELETE CASCADE,
    bowling_team_id VARCHAR(50) REFERENCES teams(id) ON DELETE CASCADE,
    
    runs_scored INTEGER,
    is_boundary BOOLEAN,
    play_type_id VARCHAR(20),
    play_type_desc VARCHAR(100),
    text TEXT,
    short_text VARCHAR(500),
    
    is_wide BOOLEAN,
    is_no_ball BOOLEAN,
    is_bye BOOLEAN,
    is_leg_bye BOOLEAN,
    
    speed_kph DECIMAL(5,2),
    speed_mph DECIMAL(5,2),
    x_coordinate DECIMAL(7,4),
    y_coordinate DECIMAL(7,4),
    hawkeye_id VARCHAR(100),
    
    batsman_runs INTEGER,
    batsman_balls_faced INTEGER,
    batsman_fours INTEGER,
    batsman_sixes INTEGER,
    
    bowler_overs DECIMAL(5,2),
    bowler_maidens INTEGER,
    bowler_wickets INTEGER,
    bowler_conceded INTEGER,
    
    team_score VARCHAR(50),
    innings_runs INTEGER,
    innings_wickets INTEGER,
    innings_run_rate DECIMAL(7,2),
    innings_required_rr DECIMAL(7,2),
    innings_target INTEGER,
    innings_session INTEGER,
    innings_day INTEGER,
    innings_lead_by INTEGER,
    innings_trail_by INTEGER,
    
    over_runs INTEGER,
    over_wickets INTEGER,
    over_maiden BOOLEAN,
    over_complete BOOLEAN,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Essential indexes for complex analytics on deliveries
CREATE INDEX idx_deliveries_competition ON deliveries(competition_id);
CREATE INDEX idx_deliveries_batsman ON deliveries(batsman_id);
CREATE INDEX idx_deliveries_bowler ON deliveries(bowler_id);
CREATE INDEX idx_deliveries_period ON deliveries(period);

CREATE TABLE IF NOT EXISTS dismissals (
    delivery_id VARCHAR(50) PRIMARY KEY REFERENCES deliveries(id) ON DELETE CASCADE,
    type VARCHAR(100),
    batsman_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    bowler_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    fielder_id VARCHAR(50) REFERENCES athletes(id) ON DELETE SET NULL,
    is_keeper BOOLEAN,
    text TEXT,
    minutes INTEGER,
    is_bowled BOOLEAN,
    bbb_timestamp BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TIER 6: Matchcard / Scorecard Cache
-- ==============================================================================

CREATE TABLE IF NOT EXISTS matchcard_batting (
    id SERIAL PRIMARY KEY,
    competition_id VARCHAR(50) REFERENCES competitions(id) ON DELETE CASCADE,
    innings_number INTEGER,
    team_name VARCHAR(255),
    player_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    player_name VARCHAR(255),
    dismissal VARCHAR(255),
    runs INTEGER,
    balls_faced INTEGER,
    fours INTEGER,
    sixes INTEGER,
    strike_rate DECIMAL(7,2),
    extras VARCHAR(100),
    total VARCHAR(100),
    total_runs INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matchcard_bowling (
    id SERIAL PRIMARY KEY,
    competition_id VARCHAR(50) REFERENCES competitions(id) ON DELETE CASCADE,
    innings_number INTEGER,
    team_name VARCHAR(255),
    player_id VARCHAR(50) REFERENCES athletes(id) ON DELETE CASCADE,
    player_name VARCHAR(255),
    overs DECIMAL(5,2),
    maidens INTEGER,
    runs_conceded INTEGER,
    wickets INTEGER,
    economy DECIMAL(7,2),
    wides INTEGER,
    no_balls INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function to auto-update 'updated_at' column
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all major tables
CREATE TRIGGER update_venues_modtime BEFORE UPDATE ON venues FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_teams_modtime BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_athletes_modtime BEFORE UPDATE ON athletes FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_events_modtime BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_competitions_modtime BEFORE UPDATE ON competitions FOR EACH ROW EXECUTE FUNCTION update_modified_column();
CREATE TRIGGER update_deliveries_modtime BEFORE UPDATE ON deliveries FOR EACH ROW EXECUTE FUNCTION update_modified_column();
