from db import query
print(query("SELECT * FROM player_name_bridge WHERE cricinfo_name LIKE '%Kohli%'"))
