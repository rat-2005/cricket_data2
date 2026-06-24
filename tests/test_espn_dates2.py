import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT c.date, l.name FROM cricket.deliveries d JOIN cricket.competitions c ON c.id=d.competition_id JOIN cricket.event_leagues el ON el.event_id=c.event_id JOIN cricket.leagues l ON l.id=el.league_id WHERE d.batsman_id = '253802' AND d.bowler_id = '311592' AND c.date > '2023-01-01'")
        print(cur.fetchall())

if __name__ == '__main__':
    test()
