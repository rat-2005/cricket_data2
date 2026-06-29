from db import query
import data_service

pid = 48405
names = data_service._get_player_names(pid)
ns = data_service._names_sql(names)

print("Names used:", ns)

rows = query(f"""
    SELECT d.batter, d.match_id, SUM(d.batter_runs) as runs
    FROM cricsheet_deliveries d
    JOIN cricsheet_matches cm ON d.match_id = cm.match_id
    WHERE d.batter IN ({ns})
      AND cm.match_type = 'ODI'
      AND d.batter != 'RG Sharma' AND d.batter != 'Rohit Sharma'
    GROUP BY d.batter, d.match_id
""")

print("Matches where batter is NOT RG Sharma or Rohit Sharma:")
for r in rows:
    print(r)
