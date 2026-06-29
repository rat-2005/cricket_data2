from db import query_one, query

pid = 28081

rows = query(f"""
    SELECT m.format, COALESCE(m.internationalClassId, 0) as int_class, m.seriesName, SUM(b.runs) as total_runs
    FROM cricinfo_batting b
    JOIN cricinfo_metadata m ON b.match_id = m.match_id
    WHERE b.playerId = {pid}
      AND b.battedType = 'yes'
      AND m.format = 'ODI'
    GROUP BY m.format, int_class, m.seriesName
    ORDER BY total_runs DESC
""")
print('Dhoni ODI series breakdown:', rows)

# what is total runs without the filters
all_odi = query_one(f"""
    SELECT SUM(b.runs) as total
    FROM cricinfo_batting b
    JOIN cricinfo_metadata m ON b.match_id = m.match_id
    WHERE b.playerId = {pid}
      AND b.battedType = 'yes'
      AND m.format = 'ODI'
""")
print('Total ODI runs without filters:', all_odi['total'])
