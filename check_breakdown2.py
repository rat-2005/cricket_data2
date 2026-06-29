from db import query_one, query

pid = 49752

res = query_one(f"""
    WITH ci_match AS (
        SELECT cp.match_id,
            SUM(cp.batsmanRuns) AS runs,
            SUM(CASE WHEN COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END) AS balls,
            SUM(CASE WHEN cp.batsmanRuns>=6 THEN 1 ELSE 0 END) AS sixes,
            SUM(CASE WHEN cp.batsmanRuns=0 AND COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END) AS dots
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid}
          AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2
          AND m.seriesName NOT ILIKE '%Under-19%'
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          AND (cp.empty IS NULL OR cp.empty = FALSE)
        GROUP BY cp.match_id
    ),
    cs_match AS (
        SELECT d.match_id,
            SUM(d.batter_runs) AS runs,
            SUM(CASE WHEN d.wides=0 THEN 1 ELSE 0 END) AS balls,
            SUM(CASE WHEN d.batter_runs>=6 THEN 1 ELSE 0 END) AS sixes,
            SUM(CASE WHEN d.batter_runs=0 AND d.wides=0 THEN 1 ELSE 0 END) AS dots
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter = 'V Kohli'
          AND cm.match_type = 'ODI'
        GROUP BY d.match_id
    ),
    combined AS (
        SELECT 
            COALESCE(ci.match_id, cs.match_id) AS match_id,
            GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS runs,
            GREATEST(COALESCE(ci.balls, 0), COALESCE(cs.balls, 0)) AS balls,
            GREATEST(COALESCE(ci.sixes, 0), COALESCE(cs.sixes, 0)) AS sixes,
            GREATEST(COALESCE(ci.dots, 0), COALESCE(cs.dots, 0)) AS dots
        FROM ci_match ci
        FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id
    )
    SELECT SUM(runs) AS total_runs, SUM(balls) AS total_balls, MAX(runs) as hs
    FROM combined
""")
print('Combined GREATEST ODI stats:', res)

cnt = query_one(f"""
    WITH ci_match AS (
        SELECT DISTINCT cp.match_id
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid} AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2 AND m.seriesName NOT ILIKE '%Under-19%'
    ),
    cs_match AS (
        SELECT DISTINCT d.match_id
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter = 'V Kohli' AND cm.match_type = 'ODI'
    )
    SELECT 
        COUNT(ci.match_id) AS ci_only,
        COUNT(cs.match_id) AS cs_only,
        COUNT(CASE WHEN ci.match_id IS NOT NULL AND cs.match_id IS NOT NULL THEN 1 END) AS both
    FROM ci_match ci
    FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id
""")
print('Match counts:', cnt)
