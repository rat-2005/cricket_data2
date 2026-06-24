import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT match_date FROM cricket.unified_deliveries WHERE tournament LIKE 'ICC Cricket World Cup, 2023%'")
        print(cur.fetchall())
        cur.execute("SELECT DISTINCT m.match_date FROM cricket.cricsheet_matches m JOIN cricket.cricsheet_deliveries d ON d.match_id = m.id WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'")
        print(cur.fetchall())

if __name__ == '__main__':
    test()
