import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def patch_recent_properly(text):
    # This is complex, let's just use simple replaces because we know the structure.
    
    # First, modify the where_clause_cricsheet appending step for recent
    pattern = r'(query = f\"\"\")'
    replacement = r"""
    recent = request.args.get('recent', 'All')
    recent_limit = ''
    if recent == 'Last 5 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 5'
    elif recent == 'Last 10 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 10'
    elif recent == 'Last 20 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 20'
    elif recent == 'Last 50 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 50'
    
    \1"""
    text = re.sub(pattern, replacement, text)
    
    # Now patch CTE queries to include m_date
    text = text.replace(
        "d.is_leg_bye\n        FROM cricket.deliveries d",
        "d.is_leg_bye,\n            c.date::date as match_date\n        FROM cricket.deliveries d"
    )
    
    text = text.replace(
        "d.is_leg_bye\n        FROM cricket.cricsheet_deliveries d",
        "d.is_leg_bye,\n            m.match_date::date as match_date\n        FROM cricket.cricsheet_deliveries d"
    )
    
    # Now patch match_aggregates
    text = text.replace(
        "match_aggregates AS (\n        SELECT \n            match_id,",
        "match_aggregates AS (\n        SELECT \n            match_id,\n            MAX(match_date) as match_date,"
    )
    
    # Finally patch the final SELECT FROM match_aggregates
    text = text.replace(
        "FROM match_aggregates\n    \"\"\"",
        "FROM (SELECT * FROM match_aggregates {recent_limit}) as recent_match_aggregates\n    \"\"\""
    )
    
    return text

def patch_faceoff_recent(text):
    # Faceoff is a bit different, it doesn't have match_aggregates CTE.
    # It just selects SUM() FROM combined_deliveries.
    # We can use a subquery: WHERE match_id IN (SELECT match_id FROM (SELECT match_id, MAX(match_date) as match_date FROM combined_deliveries GROUP BY match_id {recent_limit}) as sub)
    # But let's leave faceoff alone for now unless needed. The user is focusing on batter/bowler.
    return text

content = patch_recent_properly(content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Recent logic patched!")
