from db import query
print(query("SELECT DISTINCT batsmanPlayerId, batsmanName FROM cricinfo_parquet WHERE match_id = 518956 AND batsmanName ILIKE '%Sharma%'"))
