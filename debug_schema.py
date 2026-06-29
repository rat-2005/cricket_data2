from db import get_conn
c = get_conn()

# 1. What playerId does cricinfo_batting use for Kohli?
print("=== cricinfo_batting for playerId=253802 ===")
r = c.execute("SELECT COUNT(*) FROM cricinfo_batting WHERE playerId = 253802").fetchone()
print("count:", r)

# 2. Sample playerIds from cricinfo_batting
print("\n=== Sample playerIds from cricinfo_batting ===")
rows = c.execute("SELECT DISTINCT playerId FROM cricinfo_batting LIMIT 10").fetchall()
for row in rows:
    print(row)

# 3. Find Kohli in cricinfo_batting by name
print("\n=== Search Kohli in cricinfo_batting by playerName ===")
rows = c.execute("SELECT DISTINCT playerId, playerName FROM cricinfo_batting WHERE playerName ILIKE '%kohli%' LIMIT 10").fetchall()
for row in rows:
    print(row)

# 4. Once we have the right playerId, check cricinfo_parquet
print("\n=== cricinfo_batting player count check ===")
r = c.execute("SELECT COUNT(DISTINCT playerId) FROM cricinfo_batting").fetchone()
print("distinct players:", r)

# 5. Check if cricinfo_parquet batsmanPlayerId matches cricinfo_batting playerId
print("\n=== Do IDs overlap between tables? ===")
r = c.execute("""
    SELECT COUNT(*) FROM cricinfo_parquet cp
    JOIN cricinfo_batting cb ON cp.batsmanPlayerId = cb.playerId
    LIMIT 1
""").fetchone()
print("join count (should be > 0):", r)
