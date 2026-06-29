import duckdb

conn = duckdb.connect(':memory:')
conn.execute('INSTALL httpfs; LOAD httpfs;')
conn.execute('CALL load_aws_credentials();')

try:
    print('Checking cricinfo_parquet schema...')
    res = conn.execute("DESCRIBE SELECT * FROM read_parquet('s3://cricket-telemetry-lake-thej/data_merged/cricinfo_parquet/data.parquet')").fetchdf()
    cols = res['column_name'].tolist()
    time_cols = [c for c in cols if 'time' in c.lower() or 'date' in c.lower() or 'hour' in c.lower() or 'min' in c.lower()]
    print('Time related columns in cricinfo_parquet:', time_cols)

    print('Checking cricsheet_deliveries schema...')
    res2 = conn.execute("DESCRIBE SELECT * FROM read_parquet('s3://cricket-telemetry-lake-thej/data_merged/cricsheet_deliveries/data.parquet')").fetchdf()
    cols2 = res2['column_name'].tolist()
    time_cols2 = [c for c in cols2 if 'time' in c.lower() or 'date' in c.lower()]
    print('Time related columns in cricsheet_deliveries:', time_cols2)

except Exception as e:
    print('Error:', e)
