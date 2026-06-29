from data_service import get_batter_stats

# 28081 is Dhoni
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

res = get_batter_stats(28081, filters)
print('Data Service Dhoni ODI Stats:', res)
