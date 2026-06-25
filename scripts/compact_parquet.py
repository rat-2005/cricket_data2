import os
import glob
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import gc
import time

# How many source files to read per batch (controls peak memory)
BATCH_SIZE = 500

def compact_folder(source_dir, target_dir, folder_name):
    """Compact thousands of tiny parquet files into exactly ONE output file."""
    files = sorted(glob.glob(os.path.join(source_dir, "*.parquet")))
    if not files:
        print(f"[{folder_name}] No parquet files found, skipping.")
        return

    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "data.parquet")

    # ── Phase 1: Build unified schema by scanning every file's footer ──
    # Reading just the schema is extremely fast (~0.1 ms per file)
    print(f"[{folder_name}] Scanning {len(files)} file schemas...")
    unified_schema = None
    for f in files:
        try:
            s = pq.read_schema(f)
            if unified_schema is None:
                unified_schema = s
            else:
                unified_schema = pa.unify_schemas(
                    [unified_schema, s], promote_options="permissive"
                )
        except Exception:
            pass

    if unified_schema is None:
        print(f"[{folder_name}] Could not determine schema, skipping.")
        return

    # ── Phase 2: Stream data in batches into ONE parquet file ──
    batches = [files[i : i + BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]
    total_rows = 0

    print(f"[{folder_name}] Writing into 1 file ({len(batches)} batches of {BATCH_SIZE})...")

    writer = pq.ParquetWriter(target_file, unified_schema)

    for i, batch in enumerate(batches):
        dfs = []
        for f in batch:
            try:
                dfs.append(pd.read_parquet(f))
            except Exception:
                pass

        if not dfs:
            continue

        merged = pd.concat(dfs, ignore_index=True)
        total_rows += len(merged)

        # Align the DataFrame columns to match the unified schema
        for field in unified_schema:
            if field.name not in merged.columns:
                merged[field.name] = None

        # Keep only the columns in the unified schema, in the correct order
        merged = merged[[field.name for field in unified_schema]]

        # Convert to Arrow and write as a row group into the SAME file
        table = pa.Table.from_pandas(merged, schema=unified_schema, safe=False)
        writer.write_table(table)

        print(f"  Batch {i + 1}/{len(batches)}: {len(merged):,} rows")
        del dfs, merged, table
        gc.collect()

    writer.close()
    print(f"[{folder_name}] Done! {total_rows:,} rows -> data.parquet\n")


def main():
    source_base = "data"
    target_base = "data_merged"

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

    print(f"Compacting ALL folders into '{target_base}' (1 file each)...\n")
    start = time.time()

    for folder in directories:
        source_dir = os.path.join(source_base, folder)
        target_dir = os.path.join(target_base, folder)
        compact_folder(source_dir, target_dir, folder)

    elapsed = time.time() - start
    print(f"All done! Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
