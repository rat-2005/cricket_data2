import psycopg2
from app import get_db_connection

def find_india_matches():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT match_date, tournament, COUNT(*)
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND match_date >= '2022-11-01'::timestamp
              AND match_date <= '2022-11-30'::timestamp
            GROUP BY match_date, tournament
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        print("ESPN top matches by ball count in Nov 2022:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    find_india_matches()
