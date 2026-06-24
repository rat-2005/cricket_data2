import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def fix_england_match_simple():
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get ICC balls for Kohli
        cur.execute("""
            SELECT unified_id, over_number, ball_in_over 
            FROM cricket.unified_deliveries
            WHERE source_database = 'ICC'
              AND match_date::date = '2022-11-10'
              AND batsman_name = 'Virat Kohli'
            ORDER BY ball_in_over, unified_id
        """)
        icc_balls = cur.fetchall()
        print(f"ICC balls: {len(icc_balls)}")
        
        # Get Cricsheet balls for Kohli in the same match
        # Match ID for 2022-11-10 India vs England
        cur.execute("""
            SELECT id FROM cricket.cricsheet_matches 
            WHERE match_date::date = '2022-11-10'
              AND (team1 ILIKE '%India%' OR team2 ILIKE '%India%')
        """)
        m = cur.fetchone()
        if not m:
            print("Match not found")
            return
        match_id = m['id']
        
        # Kohli's athlete ID
        cur.execute("SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli'")
        batsman_id = cur.fetchone()['id']
        
        cur.execute("""
            SELECT batsman_runs 
            FROM cricket.cricsheet_deliveries
            WHERE match_id = %s AND batsman_id = %s
            ORDER BY id
        """, (match_id, batsman_id))
        cricsheet_balls = cur.fetchall()
        print(f"Cricsheet balls: {len(cricsheet_balls)}")
        
        if len(icc_balls) == len(cricsheet_balls) and len(icc_balls) > 0:
            for i in range(len(icc_balls)):
                icc_id = icc_balls[i]['unified_id']
                runs = cricsheet_balls[i]['batsman_runs']
                cur.execute("""
                    UPDATE cricket.unified_deliveries
                    SET batsman_runs = %s
                    WHERE unified_id = %s
                """, (runs, icc_id))
            conn.commit()
            print(f"Updated {len(icc_balls)} balls for Kohli vs England!")

if __name__ == '__main__':
    fix_england_match_simple()
