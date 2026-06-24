from app import get_db_connection

query = """
    WITH combined_deliveries AS (
        SELECT 
            d.competition_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        WHERE d.batsman_id = %s AND c.class_name IN ('T20', 'Twenty20', 'IPL', 'Women T20', 'Women''s T20', 'Other T20') AND c.event_id IN (SELECT el.event_id FROM cricket.event_leagues el JOIN cricket.leagues l ON el.league_id = l.id WHERE l.name = %s)
        
        UNION ALL
        
        SELECT 
            d.match_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE d.batsman_id = %s AND m.format IN ('T20', 'Twenty20', 'IT20', 'ODI', 'Test', 'MD') AND 
            m.match_date IN (
                SELECT DISTINCT match_date::date 
                FROM cricket.unified_deliveries 
                WHERE tournament = %s
            )
        
    ),
    match_aggregates AS (
        SELECT 
            match_id,
            SUM(batsman_runs) as match_score,
            SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END) as match_dots,
            SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END) as match_sixes,
            SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END) as match_balls_faced
        FROM combined_deliveries
        GROUP BY match_id
    )
    SELECT 
        SUM(match_score)::integer as total_runs,
        SUM(match_sixes)::integer as total_sixes,
        SUM(match_balls_faced)::integer as balls_faced,
        MAX(match_score)::integer as highest_score,
        SUM(match_dots)::integer as dot_balls
    FROM match_aggregates
"""

params = ['253802', "ICC Men's T20 World Cup, 2024", '253802', "ICC Men's T20 World Cup, 2024"]

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(query, params)
        print("Result:", cur.fetchone())
