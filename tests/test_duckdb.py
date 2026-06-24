import duckdb
import os
import json
import decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

con = duckdb.connect()

def setup():
    tables = ["deliveries", "dismissals", "cricsheet_matches", "cricsheet_deliveries", "competitions", "leagues", "event_leagues", "athletes"]
    for t in tables:
        path = f"data/{t}.parquet"
        if os.path.exists(path):
            con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('{path}')")
        else:
            print(f"Warning: {path} not found")

setup()

def get_player_stats(athlete_id):
    batting_query = """
    WITH combined_deliveries AS (
        SELECT 
            d.batsman_id as athlete_id,
            c.class_name as format,
            d.competition_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye,
            l.name as league_name
        FROM deliveries d
        JOIN competitions c ON c.id = d.competition_id
        LEFT JOIN event_leagues el ON c.event_id = el.event_id
        LEFT JOIN leagues l ON el.league_id = l.id
        WHERE d.batsman_id = ?
        
        UNION ALL
        
        SELECT 
            d.batsman_id as athlete_id,
            CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
            d.match_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye,
            NULL as league_name
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches m ON m.id = d.match_id
        WHERE d.batsman_id = ?
    ),
    match_aggregates AS (
        SELECT 
            athlete_id, 
            CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END as format,
            match_id,
            SUM(batsman_runs) as match_score,
            SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END) as match_dots,
            SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END) as match_sixes,
            SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END) as match_balls_faced
        FROM combined_deliveries
        GROUP BY athlete_id, CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END, match_id
    )
    SELECT 
        format,
        SUM(match_score)::integer as total_runs,
        SUM(match_sixes)::integer as total_sixes,
        SUM(match_balls_faced)::integer as balls_faced,
        MAX(match_score)::integer as highest_score,
        SUM(match_dots)::integer as dot_balls
    FROM match_aggregates
    GROUP BY format
    """
    
    bowling_query = """
    WITH combined_bowling AS (
        SELECT 
            d.bowler_id as athlete_id,
            c.class_name as format,
            d.competition_id as match_id,
            CASE WHEN dis.delivery_id IS NOT NULL THEN 1 ELSE 0 END as is_wicket,
            d.bowler_conceded,
            d.bowler_overs,
            l.name as league_name
        FROM deliveries d
        JOIN competitions c ON c.id = d.competition_id
        LEFT JOIN dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
        LEFT JOIN event_leagues el ON c.event_id = el.event_id
        LEFT JOIN leagues l ON el.league_id = l.id
        WHERE d.bowler_id = ?
        
        UNION ALL
        
        SELECT 
            d.bowler_id as athlete_id,
            CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
            d.match_id as match_id,
            CASE WHEN d.dismissal_type IS NOT NULL AND d.dismissal_type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
            CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END ELSE d.runs_scored END as bowler_conceded,
            CASE WHEN d.is_wide=TRUE OR d.is_no_ball=TRUE THEN 0 ELSE 1.0/6.0 END as bowler_overs,
            NULL as league_name
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches m ON m.id = d.match_id
        WHERE d.bowler_id = ?
    ),
    match_aggregates AS (
        SELECT 
            athlete_id, 
            CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END as format,
            match_id,
            SUM(is_wicket) as match_wickets,
            SUM(bowler_conceded) as match_runs_conceded,
            SUM(bowler_overs) as match_overs_bowled
        FROM combined_bowling
        GROUP BY athlete_id, CASE WHEN league_name = 'Indian Premier League' THEN 'IPL' ELSE format END, match_id
    )
    SELECT 
        format,
        SUM(match_wickets)::integer as total_wickets,
        SUM(match_runs_conceded)::integer as runs_conceded,
        SUM(match_overs_bowled) as overs_bowled,
        -- Best bowling: highest wickets, then lowest runs
        MAX(match_wickets) as best_wickets,
        MIN(CASE WHEN match_wickets = (SELECT MAX(m2.match_wickets) FROM match_aggregates m2 WHERE m2.format = match_aggregates.format) THEN match_runs_conceded ELSE NULL END) as best_runs
    FROM match_aggregates
    GROUP BY format
    """
    
    try:
        batting_df = con.execute(batting_query, (athlete_id, athlete_id)).df()
        bowling_df = con.execute(bowling_query, (athlete_id, athlete_id)).df()
        print("Batting stats:")
        print(batting_df)
        print("\nBowling stats:")
        print(bowling_df)
    except Exception as e:
        print("Error:", e)

# test MS Dhoni
get_player_stats("253802")
