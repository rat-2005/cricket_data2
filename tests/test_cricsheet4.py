import psycopg2
import psycopg2.extras
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM cricket.cricsheet_matches WHERE id IN ('1407870', '1407871')")
            print(cur.fetchall())
            
            cur.execute("SELECT DISTINCT batsman_id, bowler_id FROM cricket.cricsheet_deliveries WHERE match_id = '1407871' LIMIT 10")
            print(cur.fetchall())

if __name__ == '__main__':
    test()
