import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.match_date::date, m.format, SUM(batsman_runs) as runs
            FROM cricket.cricsheet_deliveries d
            JOIN cricket.cricsheet_matches m ON m.id = d.match_id
            WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'
              AND m.match_date::date NOT IN (
                  SELECT c2.date::date
                  FROM cricket.deliveries d2
                  JOIN cricket.competitions c2 ON c2.id = d2.competition_id
                  WHERE d2.batsman_id = '253802' AND d2.bowler_id = '311592'
              )
            GROUP BY m.match_date::date, m.format
            ORDER BY m.match_date::date
        """)
        for row in cur.fetchall():
            print(row)
        
if __name__ == '__main__':
    test()
