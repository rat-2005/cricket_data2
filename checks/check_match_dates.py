from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT m.match_date, m.team1, m.team2
            FROM cricket.cricsheet_matches m
            WHERE m.match_date IN (
                SELECT DISTINCT match_date 
                FROM cricket.unified_deliveries 
                WHERE tournament = 'ICC Men''s T20 World Cup, 2024'
            )
        """)
        print(cur.fetchall())
