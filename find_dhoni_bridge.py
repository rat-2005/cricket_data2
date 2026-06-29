from db import query
rows = query("""
    SELECT DISTINCT internal_id, cricinfo_name, cricsheet_name 
    FROM player_name_bridge 
    WHERE cricinfo_name ILIKE '%Dhoni%'
""")
print('Dhoni from bridge:', rows)
