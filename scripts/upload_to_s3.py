import os
import time
import duckdb

S3_BUCKET = "s3://cricket-telemetry-lake-thej/data_merged"

directories = [
    "cricinfo_batting",
    "cricinfo_bowling",
    "cricinfo_fow",
    "cricinfo_innings",
    "cricinfo_metadata",
    "cricinfo_parquet",
    "cricinfo_partnerships",
    "cricsheet_deliveries",
    "cricsheet_matches",
    "cricsheet_people",
]

def main():
    print("Starting S3 Upload using DuckDB...\n")
    start = time.time()
    
    con = duckdb.connect()
    print("Loading AWS credentials...")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    # In GitHub Actions, standard AWS env vars are set:
    # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    # load_aws_credentials() automatically picks these up.
    con.execute("CALL load_aws_credentials(); SET s3_region='ap-south-1';")
    
    for folder in directories:
        local_path = f"data_merged/{folder}/data.parquet"
        if os.path.exists(local_path):
            s3_path = f"{S3_BUCKET}/{folder}/data.parquet"
            print(f"Uploading {local_path} -> {s3_path} ...")
            try:
                con.execute(f"COPY (SELECT * FROM read_parquet('{local_path}')) TO '{s3_path}' (FORMAT PARQUET)")
                print(f"  [SUCCESS] {folder} uploaded.")
            except Exception as e:
                print(f"  [ERROR] {folder} failed: {e}")
        else:
            print(f"[{folder}] No local merged file found at {local_path}. Skipping.")
            
    elapsed = time.time() - start
    print(f"\nAll done! Total upload time: {elapsed:.1f}s")
    con.close()

if __name__ == "__main__":
    main()
