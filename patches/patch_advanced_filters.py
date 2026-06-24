import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def patch_filters(text):
    # Find where the venue filter ends and phase begins
    pattern = r'(if venue_filter != \'All\':.*?where_cricsheet\.append\("1=0"\)\s+)(if phase_filter)'
    
    # We will inject the new filters here
    injection = r"""\1
    opponent_filter = request.args.get('opponent', 'All')
    if opponent_filter != 'All':
        where_d.append(f"d.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%%{opponent_filter}%%' OR abbreviation ILIKE '%%{opponent_filter}%%')")
        where_cricsheet.append(f"(m.team1 ILIKE '%%{opponent_filter}%%' OR m.team2 ILIKE '%%{opponent_filter}%%')")
        
    bowling_type = request.args.get('bowling_type', 'All')
    if bowling_type != 'All':
        where_d.append(f"d.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')")
        where_cricsheet.append(f"d.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')")
        
    year_filter = request.args.get('year', 'All')
    if year_filter != 'All':
        where_d.append("EXTRACT(YEAR FROM c.date::date) = %s")
        params_d.append(year_filter)
        where_cricsheet.append("EXTRACT(YEAR FROM m.match_date::date) = %s")
        params_cricsheet.append(year_filter)
        
    innings_filter = request.args.get('innings', 'All')
    if innings_filter != 'All':
        if innings_filter in ['1', '2', '3', '4']:
            where_d.append(f"d.period = {innings_filter}")
            where_cricsheet.append(f"d.innings = {innings_filter}")
            
    \2"""
    return re.sub(pattern, injection, text, flags=re.DOTALL)

def patch_stats(text):
    # Find where the venue ends and where_clause_d begins
    pattern = r"(venue = request\.args\.get\('venue', 'All'\).*?)(# We will build the where clauses dynamically)"
    
    injection = r"""\1
    opponent = request.args.get('opponent', 'All')
    bowling_type = request.args.get('bowling_type', 'All')
    year = request.args.get('year', 'All')
    innings = request.args.get('innings', 'All')
    \2"""
    
    text = re.sub(pattern, injection, text, flags=re.DOTALL)
    
    # Find where the venue filter is added to where_d
    pattern2 = r"(if venue != 'All':.*?where_cricsheet\.append\(\"1=0\"\)\s+)(where_clause_d = \" AND \"\.join\(where_d\))"
    
    injection2 = r"""\1
    if opponent != 'All':
        where_d.append(f"d.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%%{opponent}%%' OR abbreviation ILIKE '%%{opponent}%%')")
        where_cricsheet.append(f"(m.team1 ILIKE '%%{opponent}%%' OR m.team2 ILIKE '%%{opponent}%%')")
        
    if bowling_type != 'All':
        where_d.append(f"d.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')")
        where_cricsheet.append(f"d.bowler_id IN (SELECT id FROM cricket.athletes WHERE bowling_style ILIKE '%%{bowling_type}%%')")
        
    if year != 'All':
        where_d.append("EXTRACT(YEAR FROM c.date::date) = %s")
        params_d.append(year)
        where_cricsheet.append("EXTRACT(YEAR FROM m.match_date::date) = %s")
        params_cricsheet.append(year)
        
    if innings != 'All':
        if innings in ['1', '2', '3', '4']:
            where_d.append(f"d.period = {innings}")
            where_cricsheet.append(f"d.innings = {innings}")
            
    \2"""
    
    return re.sub(pattern2, injection2, text, flags=re.DOTALL)

content = patch_filters(content)
content = patch_stats(content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied advanced filters!")
