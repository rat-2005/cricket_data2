import duckdb
import os
import time
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')

con = duckdb.connect(':memory:')
print("Loading postgres...")
con.execute('LOAD postgres;')
print("Attaching...")
con.execute(f"ATTACH '{db_url}' AS pg (TYPE POSTGRES);")
print("Attached!")

print("Checking tables...")
tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='cricket'").fetchall()
print(tables)
