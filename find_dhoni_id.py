from db import query

rows = query("""
    SELECT DISTINCT cp.batsmanPlayerId
    FROM cricinfo_parquet cp
    JOIN cricinfo_batting b ON cp.match_id = b.match_id AND cp.inningNumber = b.inningNumber
    WHERE b.playerId = 28081
    LIMIT 10
""")
print('MS Dhoni Parquet IDs:', rows)
