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
              AND match_date >= '2022-11-08'
              AND match_date <= '2022-11-12'
            GROUP BY match_date
        """)
        print("ESPN Kohli matches around Nov 10:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    count_balls()
