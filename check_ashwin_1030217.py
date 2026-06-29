from db import query
print(query("SELECT COUNT(*), SUM(CASE WHEN isWicket THEN 1 ELSE 0 END) FROM cricinfo_parquet WHERE match_id = 1030217 AND bowlerPlayerId = 12894"))
print(query("SELECT * FROM cricinfo_parquet WHERE match_id = 1030217 AND bowlerPlayerId = 12894 AND isWicket = TRUE LIMIT 20"))
