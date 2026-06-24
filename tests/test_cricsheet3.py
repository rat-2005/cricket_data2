import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT m.id, m.match_date FROM cricket.cricsheet_matches m WHERE m.match_date = '2023-11-19'")
        print(cur.fetchall())
        
        cur.execute("SELECT DISTINCT bowler_name, batsman_name FROM cricket.cricsheet_deliveries WHERE match_id = (SELECT id FROM cricket.cricsheet_matches WHERE match_date = '2023-11-19' LIMIT 1)")
        print(cur.fetchall())

if __name__ == '__main__':
    test()
