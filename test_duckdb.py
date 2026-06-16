import os
import duckdb
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get("DATABASE_URL")

db = duckdb.connect()
db.execute("INSTALL postgres;")
db.execute("LOAD postgres;")
db.execute(f"ATTACH '{DB_URL}' AS pg (TYPE postgres);")

print("Batters:", db.execute("SELECT COUNT(*) FROM pg.cricket.player_match_performances WHERE is_batting=TRUE").fetchone())
print("Null Athlete Batters:", db.execute("SELECT COUNT(*) FROM pg.cricket.player_match_performances WHERE is_batting=TRUE AND athlete_id IS NULL").fetchone())

print("\nTry alternative query without JOIN:")
df = db.execute("""
    SELECT 
        athlete_id, 
        SUM(runs) as total_runs
    FROM pg.cricket.player_match_performances
    WHERE is_batting = TRUE
    GROUP BY athlete_id
    ORDER BY total_runs DESC NULLS LAST 
    LIMIT 5;
""").df()
print(df)

# Check deliveries table for runs instead!
print("\nTry deliveries table:")
df_del = db.execute("""
    SELECT 
        batsman_id,
        SUM(runs_scored) as total_runs
    FROM pg.cricket.deliveries
    GROUP BY batsman_id
    ORDER BY total_runs DESC NULLS LAST 
    LIMIT 5;
""").df()
print(df_del)
