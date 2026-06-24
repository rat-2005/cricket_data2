import psycopg2
from app import get_db_connection

def check_cricsheet():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, date, team1, team2, match_type 
            FROM cricket.cricsheet_matches
            WHERE date >= '2022-11-09' AND date <= '2022-11-11'
              AND (team1 ILIKE '%India%' OR team2 ILIKE '%India%')
        """)
        print("Cricsheet matches:")
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    check_cricsheet()
