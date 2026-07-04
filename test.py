
import duckdb
conn = duckdb.connect(':memory:')
print(conn.execute('DESCRIBE SELECT * FROM read_parquet(''data/player_name_bridge.parquet'')').fetchall())

