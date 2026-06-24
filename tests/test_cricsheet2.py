import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.match_date, d.batsman_runs 
            FROM cricket.cricsheet_deliveries d 
            JOIN cricket.cricsheet_matches m ON m.id = d.match_id 
            WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'
            AND m.match_date IN (
                SELECT DISTINCT match_date::date 
                FROM cricket.unified_deliveries 
                WHERE tournament LIKE 'ICC Cricket World Cup, 2023%'
            )
        """)
        print(len(cur.fetchall()))

if __name__ == '__main__':
    test()
