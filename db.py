"""
db.py — DuckDB S3 Connection Manager

Singleton connection to DuckDB that reads all cricket data
directly from S3 Parquet files. No PostgreSQL needed.

Provides:
  - get_conn()    → raw DuckDB connection
  - query(sql)    → list of dicts
  - query_one(sql)→ single dict
  - query_value() → single scalar
"""
import duckdb
import numpy as np
import pandas as pd

S3_BUCKET = "s3://cricket-telemetry-lake-thej/data_merged"

_conn = None


def sync_parquet_files(target_dir='data'):
    """Downloads all necessary Parquet files from S3 to the local target_dir."""
    print(f"Syncing parquet files locally from S3 to {target_dir}...")
    import os
    os.makedirs(target_dir, exist_ok=True)
    temp_conn = duckdb.connect(":memory:")
    try:
        temp_conn.execute("INSTALL httpfs; LOAD httpfs; CALL load_aws_credentials(); SET s3_region='ap-south-1';")
        
        tables = [
            "cricinfo_parquet", "cricinfo_batting", "cricinfo_bowling",       
            "cricinfo_innings", "cricinfo_fow", "cricinfo_partnerships",  
            "cricsheet_deliveries", "cricinfo_metadata", "cricsheet_matches",   
            "cricsheet_people"
        ]
        
        for t in tables:
            s3_path = f"{S3_BUCKET}/{t}/data.parquet"
            local_path = f"{target_dir}/{t}.parquet"
            print(f"Downloading {t}...")
            # Use COPY to download efficiently
            temp_conn.execute(f"COPY (SELECT * FROM read_parquet('{s3_path}')) TO '{local_path}' (FORMAT PARQUET)")
            
        print("Parquet sync complete.")
    except Exception as e:
        print(f"Failed to sync parquet files: {e}")
        raise RuntimeError(f"S3 Download Failed: {e}")
    finally:
        temp_conn.close()

def reload_db():
    """Forces the global connection to be re-initialized (e.g. after a daily sync)."""
    global _conn
    if _conn:
        _conn.close()
    _conn = None
    get_conn()

def safe_hot_swap():
    """Downloads new files to data_temp, atomically replaces data/, and reloads db."""
    import os
    import shutil
    
    print("Starting safe hot-swap...")
    # 1. Download everything to a fresh data_temp folder
    if os.path.exists('data_temp'):
        shutil.rmtree('data_temp')
    sync_parquet_files(target_dir='data_temp')
    
    # 2. Swap the folders atomically
    if os.path.exists('data_old'):
        shutil.rmtree('data_old')
    
    if os.path.exists('data'):
        os.rename('data', 'data_old')
        
    os.rename('data_temp', 'data')
    print("Swapped data folders. Reloading DuckDB...")
    
    # 3. Reload the global DuckDB connection
    reload_db()
    
    # 4. Cleanup
    if os.path.exists('data_old'):
        try:
            shutil.rmtree('data_old')
        except Exception as e:
            print(f"Warning: could not delete data_old: {e}")
            
    print("Hot-swap complete! Zero downtime.")


import threading
_init_lock = threading.Lock()

def get_conn():
    """Get or create the singleton DuckDB connection reading from local data/.

    Uses a local 'conn' variable during initialization and only assigns
    to the global _conn AFTER everything succeeds. This prevents partially-
    initialized connections from being reused on error.
    """
    global _conn
    if _conn is not None:
        return _conn

    with _init_lock:
        if _conn is not None:
            return _conn
            
        import os
        # Check if local data exists and is valid, if not, sync it
        if not os.path.exists('data') or not os.path.exists('data/cricinfo_parquet.parquet') or os.path.getsize('data/cricinfo_parquet.parquet') < 1000:
            sync_parquet_files()

    print("Initializing DuckDB with local Parquet access...")
    import time
    max_retries = 3
    for attempt in range(max_retries):
        conn = duckdb.connect(":memory:")

        try:
            # ── Views for MASSIVE tables — query locally ─────────────
            large_tables = [
                "cricinfo_parquet",       
                "cricinfo_batting",       
                "cricinfo_bowling",       
                "cricinfo_innings",       
                "cricinfo_fow",           
                "cricinfo_partnerships",  
                "cricsheet_deliveries",   
            ]
            for t in large_tables:
                path = f"data/{t}.parquet"
                conn.execute(
                    f"CREATE OR REPLACE VIEW {t} AS "
                    f"SELECT * FROM read_parquet('{path}')"
                )

            # ── Materialize SMALL lookup tables into RAM (instant access) ─
            small_tables = [
                "cricinfo_metadata",   
                "cricsheet_matches",   
                "cricsheet_people",    
            ]
            for t in small_tables:
                path = f"data/{t}.parquet"
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {t} AS "
                    f"SELECT * FROM read_parquet('{path}')"
                )

            # ── player_name_bridge: internal ESPN ID → cricsheet player name ──
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_name_bridge AS
                SELECT DISTINCT
                    b.playerId    AS internal_id,
                    b.playerName  AS cricinfo_name,
                    COALESCE(p.name, b.playerName) AS cricsheet_name
                FROM (SELECT DISTINCT playerId, playerName
                      FROM cricinfo_batting
                      WHERE playerName IS NOT NULL) b
                LEFT JOIN cricsheet_people p ON
                    p.name IS NOT NULL
                    AND UPPER(LEFT(b.playerName, 1)) = UPPER(LEFT(p.name, 1))
                    AND UPPER(SPLIT_PART(b.playerName, ' ', -1))
                        = UPPER(SPLIT_PART(p.name, ' ', -1))
            """)

            # ── cricinfo_match_ids: deduplicate cricsheet supplements ─────
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cricinfo_match_ids AS
                SELECT DISTINCT match_id FROM cricinfo_metadata
            """)

            # ── player_primary_team: most frequent team played for ────────
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_primary_team AS
                WITH team_counts AS (
                    SELECT playerId, teamName, COUNT(*) as matches
                    FROM cricinfo_batting
                    GROUP BY playerId, teamName
                ),
                ranked_teams AS (
                    SELECT playerId, teamName,
                           ROW_NUMBER() OVER (PARTITION BY playerId ORDER BY matches DESC) as rn
                    FROM team_counts
                ),
                total_matches AS (
                    SELECT playerId, SUM(matches) as total_matches
                    FROM team_counts
                    GROUP BY playerId
                )
                SELECT r.playerId, r.teamName AS primary_team, t.total_matches
                FROM ranked_teams r
                JOIN total_matches t ON r.playerId = t.playerId
                WHERE r.rn = 1
            """)

            # ── cricinfo_player_styles: internal ESPN ID -> bowling/batting styles ──
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cricinfo_player_styles AS
                SELECT playerId, MAX(battingStyle) AS battingStyle, MAX(bowlingStyle) AS bowlingStyle
                FROM (
                    SELECT playerId, battingStyle, NULL AS bowlingStyle FROM cricinfo_batting WHERE battingStyle IS NOT NULL
                    UNION ALL
                    SELECT playerId, NULL AS battingStyle, bowlingStyle FROM cricinfo_bowling WHERE bowlingStyle IS NOT NULL
                )
                GROUP BY playerId
            """)

            # Only assign global AFTER full success
            _conn = conn
            print("DuckDB ready — all S3 views and lookup tables created.")
            return _conn

        except Exception as e:
            conn.close()
            print(f"DuckDB S3 connection failed (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                _conn = None
                raise RuntimeError(f"DuckDB init failed after {max_retries} attempts: {e}") from e
            time.sleep(2)

    return _conn


# ── Query helpers ────────────────────────────────────────────────

def query(sql, params=None):
    """Execute SQL, return results as list[dict]."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Build dicts natively to avoid pandas converting NULL to NaN
        out = []
        for row in rows:
            # Check for float NaN which might still slip through from DuckDB aggregations
            d = {}
            for k, v in zip(cols, row):
                is_missing = False
                try:
                    miss = pd.isna(v)
                    if isinstance(miss, (bool, np.bool_)) and miss:
                        is_missing = True
                except ValueError:
                    pass
                
                if is_missing:
                    d[k] = None
                else:
                    d[k] = v
            out.append(d)
        return out
    finally:
        cursor.close()


def query_one(sql, params=None):
    """Execute SQL, return first row as dict (or empty dict)."""
    rows = query(sql, params)
    return rows[0] if rows else {}


def query_value(sql, params=None):
    """Execute SQL, return a single scalar value (or None)."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        result = cursor.execute(sql, params or [])
        row = result.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
