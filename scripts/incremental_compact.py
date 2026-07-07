import os
import glob
import time
import duckdb
import gc

# 10 directories we need to compact
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

def incremental_compact(source_base, target_base, folder_name):
    source_dir = os.path.join(source_base, folder_name)
    target_dir = os.path.join(target_base, folder_name)
    target_file = os.path.join(target_dir, "data.parquet")
    
    # 1. Get all individual parquet files
    all_files = sorted(glob.glob(os.path.join(source_dir, "*.parquet")))
    if not all_files:
        print(f"[{folder_name}] No source files found.")
        return

    os.makedirs(target_dir, exist_ok=True)
    
    # 2. Check if merged file exists and find which match_ids it already has
    existing_match_ids = set()
    con = duckdb.connect(":memory:")
    
    if os.path.exists(target_file):
        try:
            if folder_name == 'cricsheet_people':
                pass
            else:
                existing_match_ids = set(
                    str(r[0]) for r in con.execute(f"SELECT DISTINCT match_id FROM read_parquet('{target_file}')").fetchall()
                    if r[0] is not None
                )
        except Exception as e:
            print(f"[{folder_name}] Could not read existing target file, will rebuild from scratch. Error: {e}")
            
    # 3. Filter only NEW files that are NOT already inside the merged file
    new_files_to_add = []
    if folder_name == 'cricsheet_people':
        new_files_to_add = all_files
    else:
        import re
        for f in all_files:
            base = os.path.basename(f)
            m = re.search(r'(\d+)', base)
            if m:
                match_id = m.group(1)
                if folder_name.startswith('cricsheet_'):
                    pass
                else:
                    if str(match_id) in existing_match_ids:
                        continue
            new_files_to_add.append(f)

    if folder_name.startswith('cricsheet_'):
        new_files_to_add = all_files

    if not new_files_to_add and os.path.exists(target_file):
        print(f"[{folder_name}] Up to date. No new files to append.")
        return
        
    print(f"[{folder_name}] Found {len(new_files_to_add)} new files to merge.")
    
    # 4. Perform the merge using DuckDB
    try:
        if not os.path.exists(target_file) or folder_name.startswith('cricsheet_'):
            print(f"[{folder_name}] Writing full file from {len(new_files_to_add)} files...")
            batch_size = 500
            first_batch = True
            
            for i in range(0, len(new_files_to_add), batch_size):
                batch = new_files_to_add[i:i+batch_size]
                if first_batch:
                    con.execute(f"CREATE TABLE temp_merged AS SELECT * FROM read_parquet({batch}, union_by_name=true)")
                    first_batch = False
                else:
                    con.execute(f"INSERT INTO temp_merged BY NAME SELECT * FROM read_parquet({batch}, union_by_name=true)")
                    
            con.execute(f"COPY temp_merged TO '{target_file}' (FORMAT PARQUET)")
        else:
            print(f"[{folder_name}] Appending {len(new_files_to_add)} files to existing data.parquet...")
            
            con.execute(f"CREATE TABLE temp_merged AS SELECT * FROM read_parquet('{target_file}')")
            
            batch_size = 500
            for i in range(0, len(new_files_to_add), batch_size):
                batch = new_files_to_add[i:i+batch_size]
                con.execute(f"INSERT INTO temp_merged BY NAME SELECT * FROM read_parquet({batch}, union_by_name=true)")
                
            con.execute(f"COPY temp_merged TO '{target_file}' (FORMAT PARQUET)")
    
        count = con.execute("SELECT count(*) FROM temp_merged").fetchone()[0]
        print(f"[{folder_name}] Done! Total rows in target: {count:,}")
    except Exception as e:
        print(f"[{folder_name}] Failed: {e}")
        
    con.close()
    gc.collect()

def main():
    source_base = "data"
    target_base = "data_merged"
    
    print("Starting Incremental Compaction...\n")
    start = time.time()
    
    for folder in directories:
        incremental_compact(source_base, target_base, folder)
        
    elapsed = time.time() - start
    print(f"All done! Total time: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
