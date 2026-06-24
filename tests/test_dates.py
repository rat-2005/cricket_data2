import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.date::date as date, 'ESPN' as source
            FROM cricket.deliveries d
            JOIN cricket.competitions c ON c.id = d.competition_id
            WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'
            GROUP BY c.date::date
        """)
        espn = set([r[0] for r in cur.fetchall()])
        
        cur.execute("""
            SELECT m.match_date::date as date, 'CRICSHEET' as source
            FROM cricket.cricsheet_deliveries d
            JOIN cricket.cricsheet_matches m ON m.id = d.match_id
            WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'
            GROUP BY m.match_date::date
        """)
        cric = set([r[0] for r in cur.fetchall()])
        
        print("ESPN dates:", sorted(list(espn)))
        print("Cricsheet dates:", sorted(list(cric)))
        print("Intersection:", espn.intersection(cric))

if __name__ == '__main__':
    test()
