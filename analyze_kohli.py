import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

kohli_id = '253802'

print("--- Virat Kohli Year-by-Year Test Runs (Combined) ---")

cur.execute("""
    WITH combined_matches AS (
        -- Cricinfo matches
        SELECT 
            EXTRACT(YEAR FROM e.date) as year, 
            e.date::date as match_date,
            c.id as source_match_id,
            'cricinfo' as source
        FROM cricket.competitions c
        JOIN cricket.events e ON c.event_id = e.id
        WHERE c.class_name = 'Test'
        
        UNION ALL
        
        -- Cricsheet matches (missing from Cricinfo)
        SELECT 
            EXTRACT(YEAR FROM m.match_date) as year, 
            m.match_date,
            m.id as source_match_id,
            'cricsheet' as source
        FROM cricket.cricsheet_matches m
        WHERE m.format IN ('Test', 'MD')
    ),
    cricinfo_runs AS (
        SELECT 
            c.id as match_id,
            SUM(d.batsman_runs) as runs
        FROM cricket.competitions c
        JOIN cricket.deliveries d ON c.id = d.competition_id
        WHERE d.batsman_id = %s AND c.class_name = 'Test'
        GROUP BY c.id
    ),
    cricsheet_runs AS (
        SELECT 
            m.id as match_id,
            SUM(d.batsman_runs) as runs
        FROM cricket.cricsheet_matches m
        JOIN cricket.cricsheet_deliveries d ON m.id = d.match_id
        WHERE d.batsman_id = %s AND m.format IN ('Test', 'MD')
        GROUP BY m.id
    )
    SELECT 
        cm.year,
        COUNT(DISTINCT cm.source_match_id) as matches,
        COALESCE(SUM(cr1.runs), 0) + COALESCE(SUM(cr2.runs), 0) as total_runs
    FROM combined_matches cm
    LEFT JOIN cricinfo_runs cr1 ON cm.source = 'cricinfo' AND cm.source_match_id = cr1.match_id
    LEFT JOIN cricsheet_runs cr2 ON cm.source = 'cricsheet' AND cm.source_match_id = cr2.match_id
    -- Only include matches where Kohli batted
    WHERE cr1.runs IS NOT NULL OR cr2.runs IS NOT NULL
    GROUP BY cm.year
    ORDER BY cm.year;
""", (kohli_id, kohli_id))

results = cur.fetchall()
total_career_runs = 0
total_matches = 0

print("Year\tMatches\tRuns")
print("-" * 30)
for row in results:
    year = int(row[0])
    matches = row[1]
    runs = row[2]
    total_career_runs += runs
    total_matches += matches
    print(f"{year}\t{matches}\t{runs}")

print("-" * 30)
print(f"Total\t{total_matches}\t{total_career_runs}")
