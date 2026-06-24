import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def get_icc_innings(conn):
    """Get all ICC innings grouped by match_date and batsman."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT match_date, batsman_name, COUNT(*) as ball_count
        FROM cricket.unified_deliveries
        WHERE source_database = 'ICC'
        GROUP BY match_date, batsman_name
    """)
    return cur.fetchall()

def map_batsman_to_id(conn, batsman_name):
    """Find the ESPN batsman_id for a given batsman_name."""
    cur = conn.cursor()
    # Simple search by exact name or substring
    cur.execute("""
        SELECT id FROM cricket.athletes 
        WHERE full_name = %s OR full_name ILIKE %s
        LIMIT 1
    """, (batsman_name, f"%{batsman_name}%"))
    res = cur.fetchone()
    return res[0] if res else None

def fix_runs():
    print("Connecting to database...")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    icc_innings = get_icc_innings(conn)
    print(f"Found {len(icc_innings)} ICC innings to process.")
    
    updated_count = 0
    
    for inning in icc_innings:
        icc_date = inning['match_date']
        batsman_name = inning['batsman_name']
        ball_count = inning['ball_count']
        
        batsman_id = map_batsman_to_id(conn, batsman_name)
        if not batsman_id:
            continue
            
        # Find ESPN match in a +/- 3 day window with the EXACT same ball count
        cur.execute("""
            SELECT match_date, COUNT(*) as espn_ball_count
            FROM cricket.unified_deliveries
            WHERE source_database = 'ESPN'
              AND batsman_id = %s
              AND match_date >= %s - INTERVAL '3 days'
              AND match_date <= %s + INTERVAL '3 days'
            GROUP BY match_date
            HAVING COUNT(*) = %s
        """, (batsman_id, icc_date, icc_date, ball_count))
        
        espn_matches = cur.fetchall()
        
        # If we found EXACTLY ONE ESPN match with the exact ball count in that window
        if len(espn_matches) == 1:
            espn_date = espn_matches[0]['match_date']
            
            # Fetch the ordered sequence of balls from ICC
            cur.execute("""
                SELECT unified_id, over_number, ball_in_over 
                FROM cricket.unified_deliveries
                WHERE source_database = 'ICC'
                  AND match_date = %s
                  AND batsman_name = %s
                ORDER BY ball_in_over, unified_id
            """, (icc_date, batsman_name))
            icc_balls = cur.fetchall()
            
            # Fetch the ordered sequence of balls from ESPN
            cur.execute("""
                SELECT batsman_runs, is_boundary
                FROM cricket.unified_deliveries
                WHERE source_database = 'ESPN'
                  AND match_date = %s
                  AND batsman_id = %s
                ORDER BY overs_actual, unified_id
            """, (espn_date, batsman_id))
            espn_balls = cur.fetchall()
            
            if len(icc_balls) == len(espn_balls):
                for i in range(len(icc_balls)):
                    icc_id = icc_balls[i]['unified_id']
                    espn_runs = espn_balls[i]['batsman_runs']
                    
                    # Update the ICC record
                    cur.execute("""
                        UPDATE cricket.unified_deliveries
                        SET batsman_runs = %s
                        WHERE unified_id = %s
                    """, (espn_runs, icc_id))
                    updated_count += 1
                    
        # Commit every few matches
        conn.commit()
        
    print(f"Successfully updated {updated_count} ICC delivery records with actual runs!")
    conn.close()

if __name__ == '__main__':
    fix_runs()
