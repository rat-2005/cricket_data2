import duckdb

print("Initializing DuckDB and loading AWS extensions...")
con = duckdb.connect()

# Install and load extensions needed for reading from S3
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")
con.execute("INSTALL aws;")
con.execute("LOAD aws;")

# Automatically load credentials from your local AWS CLI
con.execute("CALL load_aws_credentials();")

s3_uri = "s3://cricket-telemetry-lake-thej/cricinfo_parquet/match_1000853_complete.parquet"
print(f"\nDirectly querying S3: {s3_uri}...\n")

# 1. Total Rows
count = con.sql(f"SELECT count(*) FROM '{s3_uri}'").fetchone()[0]
print(f"Total Deliveries (Rows): {count}")

# 2. Sample the sweet telemetry data!
print("\n--- Telemetry Sample (First 5 balls with pitch data) ---")
telemetry_df = con.sql(f"""
    SELECT 
        inningNumber,
        overNumber, 
        ballNumber,
        batsmanPlayerId,
        bowlerPlayerId,
        title AS "Bowler to Batter",
        totalRuns,
        pitchLine, 
        pitchLength, 
        wagonX, 
        wagonY 
    FROM '{s3_uri}' 
    WHERE pitchLine IS NOT NULL 
    LIMIT 5
""").df()
print(telemetry_df.to_string(index=False))

# 3. Check what other columns we captured
cols = con.sql(f"DESCRIBE SELECT * FROM '{s3_uri}'").df()
print(f"\nTotal Columns Captured: {len(cols)}")
print("Some interesting columns:", ", ".join(cols['column_name'].tolist()[:15]) + "...")
