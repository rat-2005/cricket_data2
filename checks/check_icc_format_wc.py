from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT format 
            FROM cricket.unified_deliveries 
            WHERE tournament LIKE 'ICC Men%%T20 World Cup%%' 
              AND source_database = 'ICC'
        """)
        print("ICC format for T20 WC:", cur.fetchall())

        cur.execute("""
            SELECT DISTINCT format 
            FROM cricket.unified_deliveries 
            WHERE tournament LIKE 'ICC Men%%T20 World Cup%%' 
        """)
        print("All format for T20 WC:", cur.fetchall())

        # Also check what batsman_id looks like for Kohli in the ICC data
        cur.execute("""
            SELECT DISTINCT batsman_id, batsman_name 
            FROM cricket.unified_deliveries 
            WHERE batsman_name LIKE '%%Kohli%%' 
              AND source_database = 'ICC'
            LIMIT 5
        """)
        print("Kohli ICC batsman_id:", cur.fetchall())

        # Check what the wagon wheel query gets with T20I format
        cur.execute("""
            SELECT COUNT(*) 
            FROM cricket.unified_deliveries u
            WHERE u.batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND u.source_database = 'ICC'
              AND u.zad IS NOT NULL AND u.zad != ''
              AND u.tournament LIKE 'ICC Men%%T20 World Cup%%'
        """)
        print("Wagon wheel count for Kohli T20 WC (all):", cur.fetchall())

        cur.execute("""
            SELECT COUNT(*) 
            FROM cricket.unified_deliveries u
            WHERE u.batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND u.source_database = 'ICC'
              AND u.zad IS NOT NULL AND u.zad != ''
              AND u.tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND u.format = 'T20I'
        """)
        print("Wagon wheel count for Kohli T20 WC (format=T20I):", cur.fetchall())

        cur.execute("""
            SELECT COUNT(*) 
            FROM cricket.unified_deliveries u
            WHERE u.batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND u.source_database = 'ICC'
              AND u.zad IS NOT NULL AND u.zad != ''
              AND u.tournament LIKE 'ICC Men%%T20 World Cup%%'
              AND u.format = 'T20'
        """)
        print("Wagon wheel count for Kohli T20 WC (format=T20):", cur.fetchall())
