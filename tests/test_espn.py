import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT c.event_id FROM cricket.deliveries d JOIN cricket.competitions c ON c.id=d.competition_id WHERE d.batsman_id = '253802' AND d.bowler_id = '311592' AND c.start_date > '2023-01-01'")
        print(len(cur.fetchall()))

if __name__ == '__main__':
    test()
