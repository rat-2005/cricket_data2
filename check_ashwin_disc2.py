from db import query
import data_service

pid = 12894
names = data_service._get_player_names(pid)
ns = data_service._names_sql(names)

print("Names used:", ns)

matches = query(f"""
    WITH ci_match AS (
        SELECT cp.match_id,
            SUM(CASE WHEN cp.isWicket THEN 1 ELSE 0 END) AS wickets
        FROM cricinfo_parquet cp
        JOIN cricinfo_metadata m ON cp.match_id = m.match_id
        WHERE cp.bowlerPlayerId = {pid} AND (cp.skipped IS NULL OR cp.skipped = FALSE) AND (cp.empty IS NULL OR cp.empty = FALSE) AND m.format = 'TEST'
        GROUP BY cp.match_id
    ),
    cs_match AS (
        SELECT d.match_id,
            SUM(CASE WHEN d.is_wicket = TRUE AND COALESCE(d.dismissal_kind,'') NOT IN ('run out','retired hurt','retired out','obstructing the field') THEN 1 ELSE 0 END) AS wickets
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.bowler IN ({ns}) AND cm.match_type = 'Test'
        GROUP BY d.match_id
    )
    SELECT 
        COALESCE(ci.match_id, cs.match_id) AS match_id,
        COALESCE(ci.wickets, 0) AS ci_wickets,
        COALESCE(cs.wickets, 0) AS cs_wickets,
        GREATEST(COALESCE(ci.wickets, 0), COALESCE(cs.wickets, 0)) AS max_wickets
    FROM ci_match ci
    FULL OUTER JOIN cs_match cs ON ci.match_id = cs.match_id
    WHERE COALESCE(ci.wickets, 0) != COALESCE(cs.wickets, 0) AND GREATEST(COALESCE(ci.wickets, 0), COALESCE(cs.wickets, 0)) > 0
""")

print("Discrepancies:")
for m in matches:
    print(m)
