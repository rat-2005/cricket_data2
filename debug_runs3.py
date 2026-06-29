from db import get_conn
c = get_conn()

r = c.execute("""
    SELECT DISTINCT seriesName, format 
    FROM cricinfo_metadata 
    WHERE seriesName ILIKE '%Under-19%' 
    LIMIT 10
""").fetchall()
for row in r:
    print(row)
