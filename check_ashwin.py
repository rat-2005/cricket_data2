from db import query
import data_service

rows = query("SELECT DISTINCT internal_id FROM player_name_bridge WHERE cricinfo_name ILIKE '%Ashwin%'")
print('Ashwin internal IDs:', rows)

filters = {'format': 'Test', 'league': 'All', 'opponent': 'All', 'phase': 'All', 'venue': 'All', 'year': 'All', 'innings': 'All', 'bowling_type': 'All', 'recent': 'All'}

for r in rows:
    pid = r['internal_id']
    stats = data_service.get_bowler_stats(pid, filters)
    if stats['wickets'] > 0:
        print(f"Stats for {pid}: {stats}")
