import duckdb

conn = duckdb.connect(':memory:')
conn.execute('INSTALL httpfs; LOAD httpfs;')
conn.execute('CALL load_aws_credentials();')

try:
    res = conn.execute("SELECT timestamp FROM read_parquet('s3://cricket-telemetry-lake-thej/data_merged/cricinfo_parquet/data.parquet') WHERE timestamp IS NOT NULL LIMIT 5").fetchdf()
    print('Sample timestamps:', res.to_dict('records'))
except Exception as e:
    print('Error:', e)
