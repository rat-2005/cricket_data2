import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def patch_recent_logic(text, stats_func):
    # 1. Add m_date to combined_deliveries
    pattern_d = r"(SELECT \n\s+d.competition_id as match_id,)(.*?)(FROM cricket.deliveries d\n\s+JOIN cricket.competitions c)"
    text = re.sub(pattern_d, r"\1\2            c.date::date as m_date,\n        \3", text, flags=re.DOTALL)
    
    pattern_c = r"(SELECT \n\s+d.match_id as match_id,)(.*?)(FROM cricket.cricsheet_deliveries d\n\s+JOIN cricket.cricsheet_matches m)"
    text = re.sub(pattern_c, r"\1\2            m.match_date::date as m_date,\n        \3", text, flags=re.DOTALL)
    
    # 2. Add m_date to match_aggregates
    pattern_agg = r"(match_aggregates AS \(\n\s+SELECT \n\s+match_id,)"
    text = re.sub(pattern_agg, r"\1\n            MAX(m_date) as match_date,", text)
    
    # 3. Add recent logic in python
    pattern_py = r"(where_clause_d = \" AND \"\.join\(where_d\).*?)(query = f\"\"\")"
    
    injection = r"""\1
    recent = request.args.get('recent', 'All')
    recent_limit = ''
    if recent == 'Last 5 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 5'
    elif recent == 'Last 10 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 10'
    elif recent == 'Last 20 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 20'
    elif recent == 'Last 50 Matches': recent_limit = 'ORDER BY match_date DESC LIMIT 50'
    
    \2"""
    text = re.sub(pattern_py, injection, text, flags=re.DOTALL)
    
    # 4. Apply recent_limit to the final SELECT FROM match_aggregates
    pattern_final = r"(FROM match_aggregates)(\n\s+\"\"\")"
    
    if stats_func == 'stats_faceoff':
        # Faceoff doesn't aggregate by match, it aggregates all at once.
        # Wait, faceoff query doesn't have match_aggregates!
        pass
    else:
        text = re.sub(pattern_final, r"FROM (SELECT * FROM match_aggregates {recent_limit}) as recent_match_aggregates\2", text)
        
    return text

# Note: The regex needs to be extremely precise or it will fail.
# Instead of complex regex, let's just do targeted string replacements.
