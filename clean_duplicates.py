import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

print("Identifying duplicates...")
# We find duplicate matches by looking for matches of the same format within 7 days 
# that share at least 5 players (either as batsman or bowler).
cur.execute("""
WITH cricinfo_players AS (
    SELECT d.competition_id as match_id, c.date::date as match_date, c.class_name as format, 
           array_agg(DISTINCT p) as players
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON c.id = d.competition_id
    CROSS JOIN LATERAL unnest(ARRAY[d.batsman_id, d.bowler_id]) AS p
    WHERE p IS NOT NULL
    GROUP BY d.competition_id, c.date, c.class_name
),
cricsheet_players AS (
    SELECT d.match_id as match_id, m.match_date as match_date, 
           CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
           array_agg(DISTINCT p) as players
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON m.id = d.match_id
    CROSS JOIN LATERAL unnest(ARRAY[d.batsman_id, d.bowler_id]) AS p
    WHERE p IS NOT NULL
    GROUP BY d.match_id, m.match_date, m.format
)
SELECT cs.match_id as cricsheet_match, cs.match_date as cs_date, ci.match_id as cricinfo_match, ci.match_date as ci_date
FROM cricsheet_players cs
JOIN cricinfo_players ci 
    ON cs.format = ci.format 
    AND ABS(cs.match_date - ci.match_date) <= 7
WHERE (
    SELECT count(*) 
    FROM unnest(cs.players) as a 
    JOIN unnest(ci.players) as b ON a = b
) >= 11;
""")

duplicates = cur.fetchall()
print(f"Found {len(duplicates)} duplicate matches.")

if len(duplicates) > 0:
    cricsheet_match_ids = tuple(row[0] for row in duplicates)
    print(f"Deleting {len(cricsheet_match_ids)} matches from Cricsheet tables...")
    cur.execute("DELETE FROM cricket.cricsheet_deliveries WHERE match_id IN %s;", (cricsheet_match_ids,))
    cur.execute("DELETE FROM cricket.cricsheet_matches WHERE id IN %s;", (cricsheet_match_ids,))
    conn.commit()
    print("Cleanup complete!")
else:
    print("No duplicates found.")

