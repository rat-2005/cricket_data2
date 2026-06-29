from db import query_one
import data_service

filters = {
    'format': 'ODI',
    'league': 'All',
    'opponent': 'All',
    'phase': 'All',
    'venue': 'All',
    'year': 'All',
    'innings': 'All',
    'bowling_type': 'All',
    'recent': 'All'
}

print('New Data Service for MS Dhoni ID 7593:')
print(data_service.get_batter_stats(7593, filters))
