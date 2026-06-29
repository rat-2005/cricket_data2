from db import query
print("Cricinfo names:")
print(query("SELECT DISTINCT playerId, player.name FROM cricinfo_batting JOIN player ON cricinfo_batting.playerId = player.id WHERE playerId IN (24698, 48405)"))
