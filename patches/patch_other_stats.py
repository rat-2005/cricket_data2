import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. stats_bowler
def patch_bowler(text):
    pattern = r"(def stats_bowler\(\):.*?venue = request\.args\.get\('venue', 'All'\).*?)(where_clause_d = \" AND \"\.join\(where_d\))"
    
    injection = r"""\1
    opponent = request.args.get('opponent', 'All')
    batting_type = request.args.get('bowling_type', 'All') # Actually used as batter_type/batting_style for bowlers
    year = request.args.get('year', 'All')
    innings = request.args.get('innings', 'All')
    
    if opponent != 'All':
        where_d.append(f"d.batting_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%%{opponent}%%' OR abbreviation ILIKE '%%{opponent}%%')")
        where_cricsheet.append(f"(m.team1 ILIKE '%%{opponent}%%' OR m.team2 ILIKE '%%{opponent}%%')")
        
    if batting_type != 'All':
        where_d.append(f"d.batsman_id IN (SELECT id FROM cricket.athletes WHERE batting_style ILIKE '%%{batting_type}%%')")
        where_cricsheet.append(f"d.batsman_id IN (SELECT id FROM cricket.athletes WHERE batting_style ILIKE '%%{batting_type}%%')")
        
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
    return re.sub(pattern, injection, text, flags=re.DOTALL)

# 2. stats_faceoff
def patch_faceoff(text):
    pattern = r"(def stats_faceoff\(\):.*?venue = request\.args\.get\('venue', 'All'\).*?)(where_clause_d = \" AND \"\.join\(where_d\))"
    
    injection = r"""\1
    year = request.args.get('year', 'All')
    innings = request.args.get('innings', 'All')
    
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
    return re.sub(pattern, injection, text, flags=re.DOTALL)

content = patch_bowler(content)
content = patch_faceoff(content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied stats_bowler and stats_faceoff filters!")
