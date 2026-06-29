from db import query
import data_service

pid = 48405
names = data_service._get_player_names(pid)
ns = data_service._names_sql(names)

dropped = query(f"""
    WITH old_cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber, SUM(d.batter_runs) AS runs
        FROM cricsheet_deliveries d JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ({ns}) AND cm.match_type = 'ODI'
        GROUP BY d.match_id, d.inning
    ),
    new_cs_match AS (
        SELECT d.match_id, d.inning AS inningNumber, SUM(d.batter_runs) AS runs
        FROM cricsheet_deliveries d JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ({ns}) AND cm.match_type = 'ODI'
          AND (
              d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
              OR d.match_id IN (SELECT match_id FROM cricinfo_parquet WHERE batsmanPlayerId = {pid})
          )
        GROUP BY d.match_id, d.inning
    )
    SELECT o.match_id, o.inningNumber, o.runs AS old_runs, COALESCE(n.runs, 0) AS new_runs
    FROM old_cs_match o LEFT JOIN new_cs_match n ON o.match_id = n.match_id AND o.inningNumber = n.inningNumber
    WHERE o.runs != COALESCE(n.runs, 0) AND o.runs > 0
""")

print("Dropped matches with runs:")
for d in dropped:
    print(d)
