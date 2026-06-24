import duckdb
import pandas as pd

# Connect to in-memory DuckDB
con = duckdb.connect()

# Find Dhoni's ID
query1 = "SELECT id, full_name FROM 'data/athletes.parquet' WHERE full_name ILIKE '%Dhoni%';"
print(con.execute(query1).df())

# Find Dhoni's ODI stats from player_stats_mv.parquet
query2 = "SELECT format, total_runs FROM 'data/player_stats_mv.parquet' WHERE athlete_id = '28081';"
print(con.execute(query2).df())
