from db import get_conn
c = get_conn()

# Get Virat Kohli's ID
pid = 49752

# Query 1: Total ODI runs in cricinfo_batting
r1 = c.execute(f"""
    SELECT SUM(b.runs) 
    FROM cricinfo_batting b 
    JOIN cricinfo_metadata m ON b.match_id = m.match_id 
    WHERE b.playerId = {pid} AND UPPER(m.format) IN ('ODI', 'LIST_A')
""").fetchone()
print(f'Total ODI runs in cricinfo_batting: {r1}')

# Query 2: Total ODI runs in cricinfo_parquet (ball by ball)
r2 = c.execute(f"""
    SELECT SUM(cp.batsmanRuns) 
    FROM cricinfo_parquet cp 
    JOIN cricinfo_metadata m ON cp.match_id = m.match_id 
    WHERE cp.batsmanPlayerId = {pid} AND UPPER(m.format) IN ('ODI', 'LIST_A')
    AND (cp.skipped IS NULL OR cp.skipped = FALSE)
""").fetchone()
print(f'Total ODI runs in cricinfo_parquet: {r2}')

# Query 3: Match ids where Kohli played ODI in cricsheet but NOT in cricinfo
names = ('V Kohli', 'Virat Kohli')
ns = ', '.join([f"'{n}'" for n in names])
r3 = c.execute(f"""
    SELECT SUM(d.batter_runs) 
    FROM cricsheet_deliveries d 
    JOIN cricsheet_matches cm ON d.match_id = cm.match_id 
    WHERE d.batter IN ({ns}) 
      AND UPPER(cm.match_type) = 'ODI' 
      AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
""").fetchone()
print(f'Total extra ODI runs from cricsheet supplement: {r3}')

# Are there duplicate match records in cricinfo metadata?
dup = c.execute(f"""
    SELECT m.match_id, count(*) as c 
    FROM cricinfo_metadata m 
    GROUP BY m.match_id HAVING count(*) > 1
""").fetchall()
print(f'Duplicate matches in metadata: {dup}')

# Let's see the total runs for "ODI" vs "List A"
list_a = c.execute(f"""
    SELECT UPPER(m.format), SUM(b.runs) 
    FROM cricinfo_batting b 
    JOIN cricinfo_metadata m ON b.match_id = m.match_id 
    WHERE b.playerId = {pid} AND UPPER(m.format) IN ('ODI', 'LIST_A')
    GROUP BY UPPER(m.format)
""").fetchall()
print(f'Breakdown by format: {list_a}')
