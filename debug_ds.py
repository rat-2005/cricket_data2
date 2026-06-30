import sys
sys.path.append("d:/cricket/fresh_data")
from db import query

res = query("SELECT objectId, name FROM player_info WHERE name LIKE '%Kohli%' LIMIT 1")
print("Kohli ID:", res)
if res:
    runs = query("SELECT SUM(runs_batter) FROM cricsheet_deliveries WHERE batter_id = ?", [res[0]['objectId']])
    print("Runs:", runs)
