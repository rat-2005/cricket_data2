import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def update_kohli_runs():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        icc_date = '2022-11-02'
        espn_date = '2022-11-03'
        batsman_name = 'Virat Kohli'
        batsman_id = '253802'
        
        print("Fetching ICC balls...")
        cur.execute("""
            SELECT unified_id, over_number, ball_in_over 
            FROM cricket.unified_deliveries
            WHERE source_database = 'ICC'
              AND match_date::date = %s
              AND batsman_name = %s
            ORDER BY ball_in_over, unified_id
        """, (icc_date, batsman_name))
        icc_balls = cur.fetchall()
        
        print("Fetching ESPN balls...")
        cur.execute("""
            SELECT batsman_runs, is_boundary
            FROM cricket.unified_deliveries
            WHERE source_database = 'ESPN'
              AND match_date::date = %s
              AND batsman_id = %s
            ORDER BY overs_actual, unified_id
        """, (espn_date, batsman_id))
        espn_balls = cur.fetchall()
        
        print(f"ICC balls: {len(icc_balls)}")
        print(f"ESPN balls: {len(espn_balls)}")
        
        if len(icc_balls) == len(espn_balls) and len(icc_balls) > 0:
            for i in range(len(icc_balls)):
                icc_id = icc_balls[i]['unified_id']
                espn_runs = espn_balls[i]['batsman_runs']
                
                cur.execute("""
                    UPDATE cricket.unified_deliveries
                    SET batsman_runs = %s
                    WHERE unified_id = %s
                """, (espn_runs, icc_id))
            conn.commit()
            print(f"Successfully updated {len(icc_balls)} balls for Kohli!")
        else:
            print("Ball counts do not match or are zero.")

if __name__ == '__main__':
    update_kohli_runs()
