import duckdb
import pandas as pd

# Connect to in-memory DuckDB
con = duckdb.connect()

query = "SELECT DISTINCT class_name FROM 'data/competitions.parquet';"
print(con.execute(query).df())
