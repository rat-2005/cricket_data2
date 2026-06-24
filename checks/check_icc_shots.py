from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        # Check what format the ICC stores for T20 World Cup
        cur.execute("""
            SELECT DISTINCT format 
            FROM cricket.unified_deliveries 
            WHERE tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND source_database = 'ICC'
        """)
        print("ICC format for T20 WC:", cur.fetchall())

        # Check shot_type data for Kohli in ICC T20 WC
        cur.execute("""
            SELECT shot_type, COUNT(*) 
            FROM cricket.unified_deliveries 
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND source_database = 'ICC'
              AND tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND shot_type IS NOT NULL AND shot_type != ''
            GROUP BY shot_type
            ORDER BY count DESC
            LIMIT 10
        """)
        print("Shot types for Kohli T20 WC:", cur.fetchall())

        # Check shot_type with format = 'T20'
        cur.execute("""
            SELECT shot_type, COUNT(*) 
            FROM cricket.unified_deliveries 
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND source_database = 'ICC'
              AND format = 'T20'
              AND tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND shot_type IS NOT NULL AND shot_type != ''
            GROUP BY shot_type
            ORDER BY count DESC
            LIMIT 10
        """)
        print("Shot types (format=T20):", cur.fetchall())
