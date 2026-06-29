from db import query_one, query

pid = 28081

# cricinfo scorecard
bat = query_one(f"""
    SELECT SUM(b.runs) as total
    FROM cricinfo_batting b
    JOIN cricinfo_metadata m ON b.match_id = m.match_id
    WHERE b.playerId = {pid}
      AND b.battedType = 'yes'
      AND m.format = 'ODI' AND COALESCE(m.internationalClassId, 0) = 2
      AND m.seriesName NOT ILIKE '%Under-19%'
""")
print('Dhoni Scorecard ODI runs:', bat)

# check mapped names
names = query("""
    SELECT DISTINCT cricsheet_name
    FROM player_name_bridge
    WHERE internal_id = ?
""", [int(pid)])
print('Dhoni cricsheet names:', names)

# check pure cricsheet ODI runs using names
if names:
    ns = ", ".join(f"'{n['cricsheet_name']}'" for n in names if n.get('cricsheet_name'))
    cs_odi = query_one(f"""
        SELECT SUM(d.batter_runs) as runs
        FROM cricsheet_deliveries d
        JOIN cricsheet_matches cm ON d.match_id = cm.match_id
        WHERE d.batter IN ({ns})
          AND cm.match_type = 'ODI'
    """)
    print('Dhoni pure Cricsheet ODI runs:', cs_odi)
