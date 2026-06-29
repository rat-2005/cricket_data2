from db import query_one

pid = 28081 # MS Dhoni

res = query_one(f"""
    WITH ci_match AS (
        SELECT cp.match_id, cp.inningNumber,
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
        GROUP BY cp.match_id, cp.inningNumber
    ),
    cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber,
            SUM(d.batter_runs) AS runs,
            SUM(CASE WHEN d.wides=0 THEN 1 ELSE 0 END) AS balls,
            SUM(CASE WHEN d.batter_runs>=6 THEN 1 ELSE 0 END) AS sixes,
            SUM(CASE WHEN d.batter_runs=0 AND d.wides=0 THEN 1 ELSE 0 END) AS dots
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter = 'MS Dhoni'
          AND cm.match_type = 'ODI'
        GROUP BY d.match_id, d.inning
    ),
    combined AS (
        SELECT 
            COALESCE(ci.match_id, cs.match_id) AS match_id,
            COALESCE(ci.inningNumber, cs.inningNumber) AS inningNumber,
            GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS runs,
            GREATEST(COALESCE(ci.balls, 0), COALESCE(cs.balls, 0)) AS balls,
            GREATEST(COALESCE(ci.sixes, 0), COALESCE(cs.sixes, 0)) AS sixes,
            GREATEST(COALESCE(ci.dots, 0), COALESCE(cs.dots, 0)) AS dots
        FROM ci_match ci
        FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id AND ci.inningNumber = cs.inningNumber
    )
    SELECT SUM(runs) AS total_runs, SUM(balls) AS total_balls, MAX(runs) as hs
    FROM combined
""")
print('Dhoni Combined ODI stats:', res)

bat = query_one(f"""
    SELECT SUM(b.runs) as total
    FROM cricinfo_batting b
    JOIN cricinfo_metadata m ON b.match_id = m.match_id
    WHERE b.playerId = {pid}
      AND b.battedType = 'yes'
      AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2
      AND m.seriesName NOT ILIKE '%Under-19%'
""")
print('Dhoni Scorecard ODI runs:', bat['total'])
