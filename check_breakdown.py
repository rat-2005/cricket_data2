from db import query_one

pid = 49752

# Parquet total ODI runs
ci_odi = query_one(f"""
    SELECT SUM(cp.batsmanRuns) as runs
    FROM cricinfo_parquet cp
    JOIN cricinfo_metadata m ON cp.match_id = m.match_id
    WHERE cp.batsmanPlayerId = {pid}
      AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2
      AND m.seriesName NOT ILIKE '%Under-19%'
      AND (cp.skipped IS NULL OR cp.skipped = FALSE)
      AND (cp.empty IS NULL OR cp.empty = FALSE)
""")
print('Parquet ODI runs:', ci_odi)

# Cricsheet total ODI runs
cs_odi = query_one(f"""
    SELECT SUM(d.batter_runs) as runs
    FROM cricsheet_deliveries d
    JOIN cricsheet_matches cm ON d.match_id = cm.match_id
    WHERE d.batter = 'V Kohli'
      AND cm.match_type = 'ODI'
      AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
""")
print('Cricsheet non-overlapping ODI runs:', cs_odi)
