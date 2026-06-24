from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # The famous Kohli six off Haris Rauf on 2022-10-23 (India vs Pakistan T20 WC)
        # This was a straight six down the ground
        cur.execute("""
            SELECT zad, over_number, ball_in_over, bowler_name, batsman_runs, shot_type, match_date
            FROM cricket.unified_deliveries
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND source_database = 'ICC'
              AND match_date::date = '2022-10-23'
              AND zad IS NOT NULL AND zad != ''
            ORDER BY over_number, ball_in_over
        """)
        print("=== Kohli vs Pakistan 2022-10-23 ===")
        for r in cur.fetchall():
            zad = r[0]
            parts = zad.split(',')
            angle = int(parts[1]) if len(parts) >= 2 else '?'
            dist = int(parts[2]) if len(parts) >= 3 else '?'
            print(f"  Over {r[1]+1}.{r[2]}  ZAD={zad}  angle={angle}° dist={dist}  runs={r[4]}  shot={r[5]}  bowler={r[3]}")
        
        # Also check a known cover drive (should be ~45° off-side)
        print("\n=== Sixes only (to check angle convention) ===")
        cur.execute("""
            SELECT zad, over_number, ball_in_over, bowler_name, shot_type, match_date
            FROM cricket.unified_deliveries
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND source_database = 'ICC'
              AND tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND zad IS NOT NULL AND zad != ''
              AND CAST(split_part(zad, ',', 3) AS INTEGER) >= 5
            ORDER BY match_date DESC
            LIMIT 15
        """)
        for r in cur.fetchall():
            zad = r[0]
            parts = zad.split(',')
            angle = int(parts[1]) if len(parts) >= 2 else '?'
            dist = int(parts[2]) if len(parts) >= 3 else '?'
            print(f"  ZAD={zad}  angle={angle}° dist={dist}  shot={r[4]}  bowler={r[3]}  date={r[5]}")
