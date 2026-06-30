from db import query
res = query("SELECT format, internationalClassId, count(1) FROM cricinfo_metadata GROUP BY format, internationalClassId")
for r in res:
    print(r)
