import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def test_fast_sql():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Finding match alignments...")
        cur.execute("""
            WITH icc_counts AS (
                SELECT match_date, batsman_name, COUNT(*) as balls
                FROM cricket.unified_deliveries
                WHERE source_database = 'ICC' AND batsman_name ILIKE '%Kohli%'
                GROUP BY match_date, batsman_name
            ),
            espn_counts AS (
                SELECT match_date, batsman_id, COUNT(*) as balls
                FROM cricket.unified_deliveries
                WHERE source_database = 'ESPN' AND batsman_id = '253802'
                GROUP BY match_date, batsman_id
            )
            SELECT i.match_date as icc_date, e.match_date as espn_date, i.balls, i.batsman_name, e.batsman_id
            FROM icc_counts i
            JOIN espn_counts e
              ON i.balls = e.balls
             AND e.match_date >= i.match_date - INTERVAL '3 days'
             AND e.match_date <= i.match_date + INTERVAL '3 days'
        """)
        
        matches = cur.fetchall()
        print(f"Found {len(matches)} matched innings.")
        
        updated_count = 0
        
        for m in matches:
            icc_date = m['icc_date']
            espn_date = m['espn_date']
            batsman_name = m['batsman_name']
            batsman_id = m['batsman_id']
            
            # Fetch balls
            cur.execute("""
                SELECT unified_id
                FROM cricket.unified_deliveries
                WHERE source_database = 'ICC'
                  AND match_date = %s
                  AND batsman_name = %s
                ORDER BY ball_in_over, unified_id
            """, (icc_date, batsman_name))
            icc_balls = cur.fetchall()
            
            cur.execute("""
                SELECT batsman_runs
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
                    
                    cur.execute("""
                        UPDATE cricket.unified_deliveries
                        SET batsman_runs = %s
                        WHERE unified_id = %s
                    """, (espn_runs, icc_id))
                    updated_count += 1
                print(f"Updated {len(icc_balls)} balls for {batsman_name} on {icc_date}")
            else:
                print(f"Mismatch: ICC {len(icc_balls)} != ESPN {len(espn_balls)} for {icc_date}")
                
        conn.commit()
        print(f"Total updated: {updated_count}")

if __name__ == '__main__':
    test_fast_sql()
