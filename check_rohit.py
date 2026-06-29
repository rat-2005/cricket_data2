from db import query
import data_service

rows = query("""
    SELECT DISTINCT internal_id, cricinfo_name, cricsheet_name 
    FROM player_name_bridge 
    WHERE cricinfo_name ILIKE '%Rohit Sharma%'
""")
print('Rohit from bridge:', rows)

pid = rows[0]['internal_id']

# Now let's compare his matches using FULL OUTER JOIN
matches = query(f"""
    WITH ci_match AS (
        SELECT cp.match_id, cp.inningNumber,
            SUM(cp.batsmanRuns) AS runs,
            SUM(CASE WHEN COALESCE(cp.wides,0)=0 THEN 1 ELSE 0 END) AS balls
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid}
          AND (cp.skipped IS NULL OR cp.skipped = FALSE)
          AND (cp.empty IS NULL OR cp.empty = FALSE)
          AND m.format = 'ODI'
        GROUP BY cp.match_id, cp.inningNumber
    ),
    cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber,
            SUM(d.batter_runs) AS runs,
            SUM(CASE WHEN d.wides=0 THEN 1 ELSE 0 END) AS balls
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ('RG Sharma', 'Rohit Sharma')
          AND cm.match_type = 'ODI'
        GROUP BY d.match_id, d.inning
    ),
    combined AS (
        SELECT 
            COALESCE(ci.match_id, cs.match_id) AS match_id,
            COALESCE(ci.inningNumber, cs.inningNumber) AS inningNumber,
            COALESCE(ci.runs, 0) AS ci_runs,
            COALESCE(cs.runs, 0) AS cs_runs,
            COALESCE(ci.balls, 0) AS ci_balls,
            COALESCE(cs.balls, 0) AS cs_balls,
            GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS max_runs,
            GREATEST(COALESCE(ci.balls, 0), COALESCE(cs.balls, 0)) AS max_balls
        FROM ci_match ci
        FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id AND ci.inningNumber = cs.inningNumber
    )
    SELECT * FROM combined 
    WHERE ci_runs != cs_runs OR ci_balls != cs_balls
    ORDER BY match_id
""")

print("Discrepancies:")
for m in matches:
    print(m)

print("Total Max Runs:", sum(m['max_runs'] for m in query(f"""
    WITH ci_match AS (
        SELECT cp.match_id, cp.inningNumber, SUM(cp.batsmanRuns) AS runs
        FROM cricinfo_parquet cp JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid} AND (cp.skipped IS NULL OR cp.skipped = FALSE) AND (cp.empty IS NULL OR cp.empty = FALSE) AND m.format = 'ODI'
        GROUP BY cp.match_id, cp.inningNumber
    ),
    cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber, SUM(d.batter_runs) AS runs
        FROM cricsheet_deliveries d JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ('RG Sharma', 'Rohit Sharma') AND cm.match_type = 'ODI'
        GROUP BY d.match_id, d.inning
    )
    SELECT GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0)) AS max_runs
    FROM ci_match ci FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id AND ci.inningNumber = cs.inningNumber
""")))
