import psycopg2
from app import get_db_connection

def fix_runs_england():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        print("Finding ICC matches where batsman_runs IS NULL...")
        cur.execute("""
            UPDATE cricket.unified_deliveries u
            SET batsman_runs = c.batsman_runs
            FROM cricket.cricsheet_deliveries c
            JOIN cricket.cricsheet_matches m ON m.id = c.match_id
            JOIN cricket.athletes a ON a.id = c.batsman_id
            WHERE u.source_database = 'ICC'
              AND u.match_date::date = m.match_date::date
              AND u.match_date::date = '2022-11-10'
              AND u.batsman_name = a.full_name
              AND u.over_number = c.over_number
              AND (
                  SELECT d2.ball_number
                  FROM cricket.cricsheet_deliveries d2
                  WHERE d2.match_id = m.id AND d2.batsman_id = a.id AND d2.over_number = c.over_number
                  ORDER BY d2.ball_number
                  LIMIT 1 OFFSET (u.ball_in_over - 1)
              ) = c.ball_number
              AND u.batsman_runs IS NULL
        """)
        conn.commit()
        print(f"Updated {cur.rowcount} rows using cricsheet!")

if __name__ == '__main__':
    fix_runs_england()
