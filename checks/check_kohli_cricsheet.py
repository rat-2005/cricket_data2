from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) 
            FROM cricket.cricsheet_deliveries d
            JOIN cricket.cricsheet_matches m ON m.id = d.match_id
            WHERE d.batsman_id = '253802' AND m.match_date IN (
                SELECT DISTINCT match_date::date 
                FROM cricket.unified_deliveries 
                WHERE tournament = 'ICC Men''s T20 World Cup, 2024'
            )
        """)
        print("Total cricsheet balls for Kohli in T20 WC 2024:", cur.fetchone()[0])
