from db import query_one

pid = 28081
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
print('Cricinfo Parquet ODI runs:', ci_odi)
