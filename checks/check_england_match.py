import psycopg2
from app import get_db_connection

def check_england_match():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT batsman_id, batting_team_id
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN' 
              AND match_date::date = '2022-11-10'
        """)
        print("Batsmen on Nov 10:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    check_england_match()
