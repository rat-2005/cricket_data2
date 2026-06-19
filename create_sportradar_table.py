import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

ddl = """
CREATE TABLE IF NOT EXISTS cricket.sportradar_pitch_data (
    id SERIAL PRIMARY KEY,
    sr_match_id VARCHAR(100),
    over_number INTEGER,
    ball_number INTEGER,
    
    -- Bowler
    bowler_id VARCHAR(100),
    bowler_name VARCHAR(255),
    bowler_country VARCHAR(10),
    
    -- Striker
    striker_id VARCHAR(100),
    striker_name VARCHAR(255),
    striker_country VARCHAR(10),
    
    -- Non-striker
    non_striker_id VARCHAR(100),
    non_striker_name VARCHAR(255),
    
    -- Bowling Params
    bowling_from VARCHAR(50),
    delivery_type VARCHAR(50),
    beat_bat BOOLEAN,
    pitch_x FLOAT,
    pitch_y FLOAT,
    extra_runs_conceded INTEGER,
    bowling_end VARCHAR(50),
    
    -- Batting Params
    connect VARCHAR(50),
    shot_type VARCHAR(50),
    hit_to_boundary BOOLEAN,
    runs_scored INTEGER,
    angle_traversed FLOAT,
    zone_played_in VARCHAR(50),
    
    -- Fielding Params
    runs_saved INTEGER,
    overthrows INTEGER,
    run_out_missed BOOLEAN,
    catch_dropped BOOLEAN,
    fielded BOOLEAN,
    fielded_wicket_keeper BOOLEAN,
    misfielded BOOLEAN,
    stumping_missed BOOLEAN,
    pressure_applied BOOLEAN,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sr_match_id, over_number, ball_number)
);

CREATE INDEX IF NOT EXISTS idx_sr_pitch_bowler ON cricket.sportradar_pitch_data(bowler_name);
CREATE INDEX IF NOT EXISTS idx_sr_pitch_striker ON cricket.sportradar_pitch_data(striker_name);
CREATE INDEX IF NOT EXISTS idx_sr_pitch_match ON cricket.sportradar_pitch_data(sr_match_id);
"""

try:
    cur.execute(ddl)
    conn.commit()
    print("Successfully created table cricket.sportradar_pitch_data")
except Exception as e:
    conn.rollback()
    print(f"Failed to create table: {e}")
finally:
    conn.close()
