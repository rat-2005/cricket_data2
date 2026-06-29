from db import query
print("Cricinfo Parquet checking names:")
print(query("SELECT DISTINCT batsmanPlayerId, batsmanName FROM cricinfo_parquet WHERE batsmanPlayerId IN (24698, 48405)"))
