import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Check if rebuild happened
cur.execute("SELECT COUNT(*) FROM cricket.player_match_performances")
pmp_count = cur.fetchone()[0]
print(f"Total PMP records: {pmp_count:,}")

# Check Kohli data
cur.execute("""
    SELECT c.class_name, SUM(pmp.runs)::INT as total_runs, COUNT(DISTINCT pmp.competitor_id) as matches
    FROM cricket.player_match_performances pmp
    JOIN cricket.athletes a ON pmp.athlete_id::VARCHAR = a.id::VARCHAR
    JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
    JOIN cricket.competitions c ON comp.competition_id::text = c.id::text
    WHERE a.full_name = 'Virat Kohli' AND pmp.is_batting = true
    GROUP BY c.class_name
""")
print("\nKohli data in PMP:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} runs ({row[2]} matches)")

# Check if there's any data with is_batting=true
cur.execute("SELECT COUNT(*) FROM cricket.player_match_performances WHERE is_batting = true")
batting_records = cur.fetchone()[0]
print(f"\nTotal batting records: {batting_records:,}")

cur.close()
conn.close()
