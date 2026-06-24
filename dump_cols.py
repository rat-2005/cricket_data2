import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL aws; LOAD aws;")
con.execute("CALL load_aws_credentials();")
s3_uri = "s3://cricket-telemetry-lake-thej/cricinfo_parquet/match_1000853_complete.parquet"
cols = con.sql(f"DESCRIBE SELECT * FROM '{s3_uri}'").df()
print(cols['column_name'].tolist())
