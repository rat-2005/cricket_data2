
import duckdb
conn = duckdb.connect(':memory:')
conn.execute('INSTALL httpfs; LOAD httpfs; CALL load_aws_credentials(); SET s3_region=''ap-south-1'';')
print(conn.execute('''
    SELECT LIST(DISTINCT EXTRACT(YEAR FROM CAST(startDate AS DATE))::INT) 
    FROM read_parquet('s3://cricket-telemetry-lake-thej/data_merged/cricinfo_metadata/data.parquet')
''').fetchall())

