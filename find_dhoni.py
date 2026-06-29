from db import query
rows2 = query("SELECT DISTINCT playerId, name FROM cricinfo_batting WHERE name LIKE '%Dhoni%' LIMIT 5")
print('Batting:', rows2)
