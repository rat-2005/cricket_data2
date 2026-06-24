import psycopg2
from app import get_db_connection

def find_espn_matches():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT match_date, batsman_id, COUNT(*) 
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND match_date >= '2022-11-08'::date 
              AND match_date <= '2022-11-12'::date 
              AND tournament ILIKE '%T20 World Cup%'
            GROUP BY match_date, batsman_id
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    find_espn_matches()
