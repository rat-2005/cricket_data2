import os
import glob
import duckdb
import time

def main():
    # The source and target base directories
    source_base = "data"
    target_base = "data_merged"
    
    # We will split massive folders into chunks of 5000 files
    # to guarantee DuckDB never OOM crashes on an 8GB machine!
    CHUNK_SIZE = 5000
    
    directories = [
        "cricinfo_fow",
        "cricinfo_innings",
        "cricinfo_metadata",
        "cricinfo_parquet",
        # Batting, Bowling, and Cricsheet already finished successfully!
    ]
    
    # Initialize an in-memory DuckDB connection
    conn = duckdb.connect()
    
    print(f"Starting extremely resilient chunked compaction into '{target_base}'...\n")
    
    for folder in directories:
        source_dir = os.path.join(source_base, folder)
        target_dir = os.path.join(target_base, folder)
        
        if not os.path.exists(source_dir):
            continue
            
        parquet_files = glob.glob(os.path.join(source_dir, "*.parquet"))
        if not parquet_files:
            continue
            
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Split files into bite-sized chunks
        chunks = [parquet_files[i:i + CHUNK_SIZE] for i in range(0, len(parquet_files), CHUNK_SIZE)]
        
        print(f"[{folder}] Compacting {len(parquet_files)} files in {len(chunks)} safe chunk(s)...")
        
        for i, chunk in enumerate(chunks):
            # If only 1 chunk, name it data.parquet. Otherwise, data_part_1.parquet, etc.
            if len(chunks) == 1:
                target_file = os.path.join(target_dir, "data.parquet")
            else:
                target_file = os.path.join(target_dir, f"data_part_{i+1}.parquet")
                
            print(f"  -> Processing Chunk {i+1}/{len(chunks)} ({len(chunk)} files)...", end=" ")
            
            # DuckDB requires forward slashes on Windows for glob paths
            paths_str = ", ".join([f"'{p.replace(chr(92), '/')}'" for p in chunk])
            
            start_time = time.time()
            
            try:
                # Drop table if exists to keep memory perfectly clean
                conn.execute("DROP TABLE IF EXISTS temp_compaction")
                
                # We specifically use a SQL LIST of paths to avoid global globbing
                copy_query = f"COPY (SELECT * FROM read_parquet([{paths_str}], union_by_name=True)) TO '{target_file}' (FORMAT PARQUET)"
                conn.execute(copy_query)
                
                compaction_time = time.time() - start_time
                print(f"SUCCESS! (Took {compaction_time:.2f}s)")
                
            except Exception as e:
                print(f"\n     [ERROR] Failed on chunk {i+1}: {e}")
                # We stop the folder but continue to the next one
                break
                
        print(f"[{folder}] Finished!\n")

if __name__ == "__main__":
    main()
