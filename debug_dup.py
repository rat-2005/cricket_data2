from db import get_conn
import json
c = get_conn()

res = c.execute("""
    SELECT DISTINCT
        internal_id   AS id,
        cricinfo_name AS full_name,
        cricinfo_name AS short_name
    FROM player_name_bridge
    WHERE cricinfo_name IS NOT NULL
      AND cricinfo_name ILIKE '%Virat%'
    ORDER BY CASE WHEN cricinfo_name ILIKE 'Virat%' THEN 1 ELSE 2 END, cricinfo_name
    LIMIT 10
""").fetchdf()

print(res)
