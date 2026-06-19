import psycopg2
import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
import time

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)

tables = ["dismissals", "cricsheet_matches", "cricsheet_deliveries", "deliveries"]
os.makedirs("data", exist_ok=True)

for table in tables:
    path = f"data/{table}.parquet"
    if os.path.exists(path) and os.path.getsize(path) > 1024:
        print(f"Skipping {table}, already exists and is not 0 bytes")
        continue
        
    print(f"Exporting {table} via pandas chunking...")
    t = time.time()
    chunksize = 200000
    writer = None
    
    try:
        # Use a server-side cursor to avoid loading millions of rows into RAM at once
        cursor = conn.cursor(name=f'fetch_{table}')
        cursor.execute(f"SELECT * FROM cricket.{table}")
        
        while True:
            records = cursor.fetchmany(size=chunksize)
            if not records:
                break
                
            # Get column names
            colnames = [desc[0] for desc in cursor.description]
            chunk_df = pd.DataFrame(records, columns=colnames)
            
            table_pa = pa.Table.from_pandas(chunk_df)
            if writer is None:
                writer = pq.ParquetWriter(path, table_pa.schema)
            writer.write_table(table_pa)
            
        cursor.close()
        if writer:
            writer.close()
        print(f" -> Finished {table} in {time.time()-t:.2f}s")
    except Exception as e:
        print(f"Failed on {table}: {e}")
        if writer:
            writer.close()
