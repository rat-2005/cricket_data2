from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.match_date, m.team1, m.team2
            FROM cricket.cricsheet_matches m
            WHERE m.match_date IN (
                SELECT DISTINCT match_date::date 
                FROM cricket.unified_deliveries 
                WHERE tournament = 'ICC Men''s T20 World Cup, 2024'
            )
            LIMIT 10
        """)
        rows = cur.fetchall()
        print(f"Matched {len(rows)} matches:")
        for r in rows:
            print(r)
