import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

print("Merging Cricsheet data into main tables...")

try:
    print("0. Inserting missing athletes from people.csv...")
    import csv
    missing_athletes = []
    with open('people.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['key_cricinfo']:
                missing_athletes.append((row['key_cricinfo'], row['name'], row['name']))
                
    cur.execute("""
        CREATE TEMP TABLE temp_athletes (id VARCHAR(50), full_name VARCHAR(255), short_name VARCHAR(100));
    """)
    from psycopg2.extras import execute_batch
    execute_batch(cur, "INSERT INTO temp_athletes (id, full_name, short_name) VALUES (%s, %s, %s)", missing_athletes)
    
    cur.execute("""
        INSERT INTO cricket.athletes (id, full_name, short_name)
        SELECT id, full_name, short_name FROM temp_athletes
        ON CONFLICT (id) DO NOTHING;
    """)
    print(f"   Inserted missing athletes.")
    
    print("1. Inserting dummy event...")
    cur.execute("""
        INSERT INTO cricket.events (id, uid, name)
        VALUES ('cricsheet_event', 'cricsheet_event_uid', 'Missing International Matches (Cricsheet)')
        ON CONFLICT (id) DO NOTHING;
    """)

    print("2. Merging competitions...")
    # Map Cricsheet format MD -> Test, T20 -> T20I, etc.
    cur.execute("""
        INSERT INTO cricket.competitions (id, event_id, date, class_name)
        SELECT 
            m.id, 
            'cricsheet_event', 
            m.match_date, 
            CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END
        FROM cricket.cricsheet_matches m
        ON CONFLICT (id) DO NOTHING;
    """)
    inserted_matches = cur.rowcount
    print(f"   Inserted {inserted_matches} matches.")

    print("3. Merging deliveries...")
    cur.execute("""
        INSERT INTO cricket.deliveries (
            id, competition_id, sequence, period, over_number, ball_in_over, batsman_id, bowler_id,
            runs_scored, is_wide, is_no_ball, is_bye, is_leg_bye, is_boundary
        )
        SELECT 
            d.match_id || '_' || d.innings || '_' || d.over_number || '_' || d.ball_number,
            d.match_id, 
            ROW_NUMBER() OVER(PARTITION BY d.match_id ORDER BY d.innings, d.over_number, d.ball_number)::integer as sequence,
            d.innings, d.over_number, d.ball_number, d.batsman_id, d.bowler_id,
            d.runs_scored, d.is_wide, d.is_no_ball, d.is_bye, d.is_leg_bye, d.is_boundary
        FROM cricket.cricsheet_deliveries d
        -- Only insert if the competition was successfully merged (e.g., skip if foreign key violation in competitions)
        WHERE EXISTS (SELECT 1 FROM cricket.competitions c WHERE c.id = d.match_id)
        ON CONFLICT (id) DO NOTHING;
    """)
    inserted_deliveries = cur.rowcount
    print(f"   Inserted {inserted_deliveries} deliveries.")
    
    print("4. Updating dismissals (wickets)...")
    cur.execute("""
        INSERT INTO cricket.dismissals (delivery_id, type)
        SELECT 
            c_del.match_id || '_' || c_del.innings || '_' || c_del.over_number || '_' || c_del.ball_number,
            c_del.dismissal_type
        FROM cricket.cricsheet_deliveries c_del
        WHERE c_del.dismissal_type IS NOT NULL
        -- Ensure the delivery was actually inserted in the main table
        AND EXISTS (SELECT 1 FROM cricket.deliveries d_main WHERE d_main.id = c_del.match_id || '_' || c_del.innings || '_' || c_del.over_number || '_' || c_del.ball_number)
        ON CONFLICT (delivery_id) DO NOTHING;
    """)
    inserted_dismissals = cur.rowcount
    print(f"   Inserted {inserted_dismissals} dismissals.")

    conn.commit()
    print("Merge successful!")

except Exception as e:
    conn.rollback()
    print(f"Error during merge: {e}")
