from db import query
print(query("SELECT DISTINCT bowlerPlayerId, bowlerName FROM cricinfo_parquet WHERE match_id = 1062573 AND bowlerName ILIKE '%Ashwin%'"))
