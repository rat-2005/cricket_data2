from db import query
import data_service

pid = 48405
names = data_service._get_player_names(pid)
ns = data_service._names_sql(names)

print("Names used:", ns)

# Test the new logic
total = query(f"""
    WITH ci_match AS (
        SELECT cp.match_id, cp.inningNumber, SUM(cp.batsmanRuns) AS runs
        FROM cricinfo_parquet cp JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.batsmanPlayerId = {pid} AND (cp.skipped IS NULL OR cp.skipped = FALSE) AND (cp.empty IS NULL OR cp.empty = FALSE) AND m.format = 'ODI'
        GROUP BY cp.match_id, cp.inningNumber
    ),
    cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber, SUM(d.batter_runs) AS runs
        FROM cricsheet_deliveries d JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ({ns}) 
          AND cm.match_type = 'ODI'
          AND (
              d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
              OR d.match_id IN (SELECT match_id FROM cricinfo_parquet WHERE batsmanPlayerId = {pid})
          )
        GROUP BY d.match_id, d.inning
    )
    SELECT SUM(GREATEST(COALESCE(ci.runs, 0), COALESCE(cs.runs, 0))) AS max_runs
    FROM ci_match ci FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id AND ci.inningNumber = cs.inningNumber
""")

print("Total Max Runs with new logic:", total[0]['max_runs'])
