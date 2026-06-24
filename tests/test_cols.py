import os
import duckdb
from dotenv import load_dotenv

load_dotenv()
db = duckdb.connect()
db.execute("INSTALL postgres; LOAD postgres;")
db.execute(f"ATTACH '{os.environ.get('DATABASE_URL')}' AS pg (TYPE postgres);")

print(db.execute("SELECT EXTRACT(YEAR FROM c.date) as year, COUNT(DISTINCT c.id) as matches, SUM(d.batsman_runs)::INT as runs FROM pg.cricket.deliveries d JOIN pg.cricket.competitions c ON d.competition_id = c.id WHERE d.batsman_id='253802' GROUP BY year ORDER BY year").df())
