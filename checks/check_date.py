import psycopg2
from app import get_db_connection

def check_date():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) 
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND match_date::date = '2022-11-10'
        """)
        print("ESPN balls on 2022-11-10:", cur.fetchone()[0])
        
        cur.execute("""
            SELECT match_date, match_title, batting_team_id, bowling_team_id
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND match_date >= '2022-11-09'::timestamp
              AND match_date <= '2022-11-11'::timestamp
            LIMIT 1
        """)
        print(cur.fetchone())

if __name__ == '__main__':
    check_date()
