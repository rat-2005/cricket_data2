import psycopg2
from app import get_db_connection

def count_balls():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT match_date, COUNT(*) 
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND batsman_id = '253802' 
              AND match_date >= '2022-11-01'::timestamp
              AND match_date <= '2022-11-30'::timestamp
            GROUP BY match_date
            ORDER BY match_date DESC
        """)
        print("ESPN Kohli Nov 2022 matches:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    count_balls()
