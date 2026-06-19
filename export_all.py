import duckdb
import os
import time
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

con = duckdb.connect(':memory:')
con.execute('LOAD postgres;')
con.execute(f"ATTACH '{db_url}' AS pg (TYPE POSTGRES);")

tables = ["competitions", "event_leagues", "leagues", "athletes", "player_stats_mv", "bowler_stats_mv", "deliveries", "dismissals", "cricsheet_matches", "cricsheet_deliveries"]

os.makedirs('data', exist_ok=True)

for table in tables:
    path = f"data/{table}.parquet"
    if os.path.exists(path):
        print(f"{path} already exists, skipping")
        continue
        
    t = time.time()
    print(f"Exporting {table}...")
    con.execute(f"COPY pg.cricket.{table} TO '{path}' (FORMAT PARQUET);")
    print(f" -> exported {table} in {time.time()-t:.2f}s")
