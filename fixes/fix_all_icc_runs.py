import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def fix_all_icc_runs():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch all ICC innings grouped by date, batsman
        print("Fetching ICC innings...")
        cur.execute("""
            SELECT match_date, batsman_name, COUNT(*) as balls
            FROM cricket.unified_deliveries
            WHERE source_database = 'ICC'
            GROUP BY match_date, batsman_name
        """)
        icc_innings = cur.fetchall()
        print(f"Found {len(icc_innings)} ICC innings.")
        
        # 2. Map all batsman_name to ESPN IDs
        print("Mapping batsman names to IDs...")
        mapped_batsmen = {}
        for row in icc_innings:
            name = row['batsman_name']
            if name not in mapped_batsmen:
                # Basic exact/ILIKE mapping
                # But wait, cricket.athletes full_name might have first names, etc.
                # Since we already have the ICC table, let's just do a quick lookup
                cur.execute("""
                    SELECT id FROM cricket.athletes 
                    WHERE full_name = %s OR full_name ILIKE %s
                    LIMIT 1
                """, (name, f"%{name}%"))
                res = cur.fetchone()
                mapped_batsmen[name] = res['id'] if res else None
                
        # 3. Process matches
        updated_count = 0
        skipped_count = 0
        
        print("Matching and updating runs...")
        for i, inning in enumerate(icc_innings):
            if i % 100 == 0:
                print(f"Processed {i}/{len(icc_innings)} innings...")
                
            icc_date = inning['match_date']
            batsman_name = inning['batsman_name']
            ball_count = inning['balls']
            batsman_id = mapped_batsmen[batsman_name]
            
            if not batsman_id:
                skipped_count += 1
                continue
                
            # Find ESPN match in window
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
            
            if len(espn_matches) == 1:
                espn_date = espn_matches[0]['match_date']
                
                # Fetch sequence
                cur.execute("""
                    SELECT unified_id 
                    FROM cricket.unified_deliveries
                    WHERE source_database = 'ICC' AND match_date = %s AND batsman_name = %s
                    ORDER BY ball_in_over, unified_id
                """, (icc_date, batsman_name))
                icc_balls = cur.fetchall()
                
                cur.execute("""
                    SELECT batsman_runs 
                    FROM cricket.unified_deliveries
                    WHERE source_database = 'ESPN' AND match_date = %s AND batsman_id = %s
                    ORDER BY overs_actual, unified_id
                """, (espn_date, batsman_id))
                espn_balls = cur.fetchall()
                
                if len(icc_balls) == len(espn_balls):
                    for j in range(len(icc_balls)):
                        icc_id = icc_balls[j]['unified_id']
                        espn_runs = espn_balls[j]['batsman_runs']
                        
                        cur.execute("""
                            UPDATE cricket.unified_deliveries
                            SET batsman_runs = %s
                            WHERE unified_id = %s
                        """, (espn_runs, icc_id))
                        updated_count += 1
                        
            conn.commit()
            
        print(f"Finished! Updated {updated_count} balls. Skipped {skipped_count} unmapped batsmen innings.")

if __name__ == '__main__':
    fix_all_icc_runs()
