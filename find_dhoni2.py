from db import query

rows = query("SELECT id, name FROM player WHERE name ILIKE '%Dhoni%'")
print('Dhoni from player table:', rows)
