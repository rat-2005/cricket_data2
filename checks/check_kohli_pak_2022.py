from app import get_db_connection

def analyze_kohli_shots():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT over_number, ball_in_over, batsman_runs, bowler_name, zad, match_date
            FROM cricket.unified_deliveries 
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli') 
              AND source_database = 'ICC' 
              AND match_date::date = '2022-10-23' 
              AND zad IS NOT NULL AND zad != '' 
            ORDER BY over_number, ball_in_over
        """)
        res = cur.fetchall()
        
        for r in res:
            over = r[0] + 1
            ball = r[1]
            runs = r[2]
            bowler = r[3]
            zad = r[4]
            
            if ball and ball > 6:
                calc_ball = (ball - 1) % 6 + 1
            else:
                calc_ball = ball
                
            print(f"Over {over}.{calc_ball} (raw {ball}) - Runs: {runs}, Bowler: {bowler}, ZAD: {zad}")

if __name__ == '__main__':
    analyze_kohli_shots()
