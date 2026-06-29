from db import query
print(query("""
    SELECT DISTINCT cp.batsmanPlayerId, pnb.cricinfo_name
    FROM cricinfo_parquet cp
    LEFT JOIN player_name_bridge pnb ON cp.batsmanPlayerId = pnb.internal_id
    WHERE cp.match_id = 1388406
"""))
