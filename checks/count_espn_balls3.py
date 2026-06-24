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
            GROUP BY match_date
            ORDER BY match_date DESC
            LIMIT 10
        """)
        print("ESPN Kohli latest matches:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    count_balls()
