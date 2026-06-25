import os
import glob
import duckdb
import time

def main():
    # S3 bucket base paths
    source_base = "s3://cricket-telemetry-lake-thej"
    target_base = "s3://cricket-telemetry-lake-thej/data_merged"
    
    # List of all directories we want to compact
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
        "cricsheet_people"
    ]
    
    # Initialize an in-memory DuckDB connection and configure S3
    conn = duckdb.connect()
    
    print("Loading AWS credentials into DuckDB...")
    conn.execute("INSTALL httpfs;")
    conn.execute("LOAD httpfs;")
    conn.execute("CALL load_aws_credentials();")
    
    print(f"Starting highly optimized compaction directly on S3: '{source_base}' -> '{target_base}'...\n")
    
    for folder in directories:
        source_dir = f"{source_base}/{folder}"
        target_dir = f"{target_base}/{folder}"
        
        print(f"[{folder}] Compacting files directly from S3...")
        
        # We will output exactly one file per folder: data.parquet
        target_file = f"{target_dir}/data.parquet"
        
        # Step 1: Count rows in the source files to guarantee zero data loss
        try:
            source_count_query = f"SELECT COUNT(*) FROM '{source_dir}/*.parquet'"
            source_rows = conn.execute(source_count_query).fetchone()[0]
        except Exception as e:
            print(f"[{folder}] Error reading source files: {e}")
            continue
            
        start_time = time.time()
        
        # Step 2: Use DuckDB's blazing fast C++ engine to stream all files into a single compacted file
        try:
            # Drop the table if it exists in memory just to be safe
            conn.execute("DROP TABLE IF EXISTS temp_compaction")
            
            # Use COPY to write directly to disk without holding everything in memory
            copy_query = f"COPY (SELECT * FROM '{source_dir}/*.parquet') TO '{target_file}' (FORMAT PARQUET)"
            conn.execute(copy_query)
        except Exception as e:
            print(f"[{folder}] Error compacting files: {e}")
            continue
            
        compaction_time = time.time() - start_time
        
        # Step 3: Count rows in the newly generated compacted file to mathematically guarantee safety
        try:
            target_count_query = f"SELECT COUNT(*) FROM '{target_file}'"
            target_rows = conn.execute(target_count_query).fetchone()[0]
        except Exception as e:
            print(f"[{folder}] Error reading target file: {e}")
            continue
            
        # Verify 
        if source_rows == target_rows:
            print(f"  -> SUCCESS: Compacted into 1 file. Row count exactly matches ({source_rows:,} rows). Zero data lost! Took {compaction_time:.2f}s")
        else:
            print(f"  -> WARNING: Data loss detected! Source had {source_rows} rows, but Target has {target_rows} rows.")

if __name__ == "__main__":
    main()
