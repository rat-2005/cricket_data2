from app import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT over_number, ball_in_over, bowler_name, zad
        FROM cricket.unified_deliveries 
        WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli') 
          AND match_date::date = '2022-11-02'
          AND source_database = 'ICC'
    """)
    res = cur.fetchall()
    boundaries = []
    for r in res:
        zad = r[3]
        if zad:
            parts = zad.split(',')
            if len(parts) >= 3:
                dist = int(parts[2])
                if dist >= 4:
                    boundaries.append(f"Over {r[0]+1}.{r[1]} - Bowler: {r[2]} - ZAD: {zad}")
    
    print(f"Found {len(boundaries)} boundaries/distance>=4:")
    for b in boundaries:
        print(b)
