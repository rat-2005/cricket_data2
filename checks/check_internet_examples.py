from app import get_db_connection

def check_examples():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # We know these specific balls and their real-world shot types
        # 12.4 Nawaz -> Slog sweep over long-on (Angle 285)
        # 18.1 Afridi -> Pulled over deep mid-wicket (Angle 339)
        # 19.5 Rauf -> Straight / Long-on six (Angle 293)
        # 19.6 Rauf -> Flick over fine leg (Angle 36)
        # 20.4 Nawaz -> Deep square leg (Angle 12)
        
        examples = [
            (12, 4, "Slog sweep over Long-On"),
            (17, 1, "Pulled over Deep Mid-Wicket"),
            (18, 5, "Straight / Long-On six"),
            (18, 6, "Flick over Fine Leg"),
            (19, 4, "Deep Square Leg")
        ]
        
        for over, ball, desc in examples:
            cur.execute("""
                SELECT over_number, ball_in_over, zad
                FROM cricket.unified_deliveries 
                WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli') 
                  AND source_database = 'ICC' 
                  AND match_date::date = '2022-10-23' 
                  AND over_number = %s
                ORDER BY ball_in_over
            """, (over,))
            
            res = cur.fetchall()
            
            # Find the nth valid ball in the over
            valid_balls = [r for r in res if r[2]]
            if len(valid_balls) >= ball:
                b = valid_balls[ball-1]
                print(f"Over {over+1}.{ball} | Real World: {desc:30} | Data Angle: {b[2].split(',')[1]}°")

if __name__ == '__main__':
    check_examples()
