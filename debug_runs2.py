from db import get_conn
c = get_conn()

pid = 49752

# Query matches in cricinfo where Kohli played in "ODI" / "LIST_A" format
r = c.execute(f"""
    SELECT m.seriesName, SUM(cp.batsmanRuns) as runs, COUNT(DISTINCT cp.match_id) as matches
    FROM cricinfo_parquet cp 
    JOIN cricinfo_metadata m ON cp.match_id = m.match_id 
    WHERE cp.batsmanPlayerId = {pid} AND UPPER(m.format) IN ('ODI', 'LIST_A')
    AND (cp.skipped IS NULL OR cp.skipped = FALSE)
    GROUP BY m.seriesName
    ORDER BY runs ASC
    LIMIT 20
""").fetchall()

print("=== Cricinfo Series Breakdown ===")
for row in r:
    print(row)

r2 = c.execute(f"""
    SELECT cm.event, SUM(d.batter_runs) as runs, COUNT(DISTINCT d.match_id) as matches
    FROM cricsheet_deliveries d 
    JOIN cricsheet_matches cm ON d.match_id = cm.match_id 
    WHERE d.batter IN ('V Kohli', 'Virat Kohli') 
      AND UPPER(cm.match_type) = 'ODI' 
      AND d.match_id NOT IN (SELECT match_id FROM cricinfo_match_ids)
    GROUP BY cm.event
    ORDER BY runs ASC
    LIMIT 20
""").fetchall()

print("\n=== Cricsheet Supplement Series Breakdown ===")
for row in r2:
    print(row)
