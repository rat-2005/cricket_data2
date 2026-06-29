from db import query
print("Internal ID 24698:")
print(query("SELECT * FROM player_name_bridge WHERE internal_id = 24698"))
print("Internal ID 48405:")
print(query("SELECT * FROM player_name_bridge WHERE internal_id = 48405"))
