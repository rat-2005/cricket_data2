from app import get_db_connection
from datetime import timedelta

def test_innings_alignment():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get Kohli's ICC innings vs Bangladesh
        cur.execute("""
            SELECT unified_id, match_date, over_number, ball_in_over, zad
            FROM cricket.unified_deliveries
            WHERE source_database = 'ICC'
              AND match_date::date = '2022-11-02'
              AND batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
            ORDER BY ball_in_over
        """)
        icc_balls = cur.fetchall()
        
        # Get Kohli's ESPN innings vs Bangladesh (Match Date is Nov 3 due to offset)
        cur.execute("""
            SELECT unified_id, match_date, over_number - 1 as over_number, overs_actual, batsman_runs, is_wide, is_no_ball
            FROM cricket.unified_deliveries
            WHERE source_database = 'ESPN'
              AND match_date::date = '2022-11-03'
              AND batsman_id = '253802'
            ORDER BY overs_actual
        """)
        espn_balls = cur.fetchall()
        
        print(f"ICC balls faced: {len(icc_balls)}")
        print(f"ESPN balls faced (including wides/noballs): {len(espn_balls)}")
        
        # Try to align them
        # Note: ICC tracks every ball including wides/noballs, ESPN also does.
        # Let's print them side-by-side
        for i in range(max(len(icc_balls), len(espn_balls))):
            icc_str = f"ICC: {icc_balls[i][2]}.{icc_balls[i][3]}" if i < len(icc_balls) else "ICC: N/A"
            espn_str = f"ESPN: Over {espn_balls[i][2]} (actual {espn_balls[i][3]}) Runs: {espn_balls[i][4]} Wide:{espn_balls[i][5]} NB:{espn_balls[i][6]}" if i < len(espn_balls) else "ESPN: N/A"
            print(f"{icc_str:<25} | {espn_str}")

if __name__ == '__main__':
    test_innings_alignment()
