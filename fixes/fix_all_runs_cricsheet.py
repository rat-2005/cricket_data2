import psycopg2
from app import get_db_connection

def fix_all_runs_cricsheet():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        print("Fixing all ICC matches where batsman_runs IS NULL using Cricsheet...")
        
        # This query updates all ICC deliveries where batsman_runs is null
        # by finding the corresponding ball in cricsheet_deliveries
        # It joins on match_date, batsman_name, over_number, and ball_in_over index
        cur.execute("""
            WITH mapped_cricsheet AS (
                SELECT 
                    m.match_date::date as match_date,
                    a.full_name as batsman_name,
                    c.over_number,
                    c.ball_number,
                    c.batsman_runs as batsman_runs,
                    ROW_NUMBER() OVER(PARTITION BY m.id, a.id, c.over_number ORDER BY c.ball_number) as ball_index
                FROM cricket.cricsheet_deliveries c
                JOIN cricket.cricsheet_matches m ON m.id = c.match_id
                JOIN cricket.athletes a ON a.id = c.batsman_id
            ),
            mapped_icc AS (
                SELECT 
                    unified_id,
                    match_date::date as match_date,
                    batsman_name,
                    over_number,
                    ball_in_over as ball_index
                FROM cricket.unified_deliveries
                WHERE source_database = 'ICC' AND batsman_runs IS NULL
            )
            UPDATE cricket.unified_deliveries u
            SET batsman_runs = c.batsman_runs
            FROM mapped_icc i
            JOIN mapped_cricsheet c 
              ON i.match_date = c.match_date 
             AND i.batsman_name = c.batsman_name
             AND i.over_number = c.over_number
             AND i.ball_index = c.ball_index
            WHERE u.unified_id = i.unified_id
        """)
        
        updated = cur.rowcount
        conn.commit()
        print(f"Successfully updated {updated} deliveries across the entire database!")

if __name__ == '__main__':
    fix_all_runs_cricsheet()
