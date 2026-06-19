import duckdb
import os
import time
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

con = duckdb.connect(':memory:')
con.execute('LOAD postgres;')
con.execute(f"ATTACH '{db_url}' AS pg (TYPE POSTGRES);")

t = time.time()
con.execute("COPY pg.cricket.cricsheet_deliveries TO 'data/cricsheet_deliveries.parquet' (FORMAT PARQUET);")
print(f"cricsheet_deliveries exported in {time.time()-t:.2f}s")

t = time.time()
con.execute("COPY pg.cricket.cricsheet_matches TO 'data/cricsheet_matches.parquet' (FORMAT PARQUET);")
print(f"cricsheet_matches exported in {time.time()-t:.2f}s")

t = time.time()
con.execute("COPY pg.cricket.deliveries TO 'data/deliveries.parquet' (FORMAT PARQUET);")
print(f"deliveries exported in {time.time()-t:.2f}s")

t = time.time()
con.execute("COPY pg.cricket.dismissals TO 'data/dismissals.parquet' (FORMAT PARQUET);")
print(f"dismissals exported in {time.time()-t:.2f}s")
