import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def inject_stats(text):
    # Find the comment right before where_clause_d
    pattern = r"(\s+# NOTE: Opponent team is tricky.*?)(where_clause_d = \" AND \"\.join\(where_d\))"
    
    injection = r"""\1
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
        if innings == '1':
            where_d.append(f"d.period = 1")
            where_cricsheet.append(f"d.innings = 1")
        elif innings == '2':
            where_d.append(f"d.period = 2")
            where_cricsheet.append(f"d.innings = 2")
        elif innings == '3':
            where_d.append(f"d.period = 3")
            where_cricsheet.append(f"d.innings = 3")
        elif innings == '4':
            where_d.append(f"d.period = 4")
            where_cricsheet.append(f"d.innings = 4")
            
    \2"""
    
    return re.sub(pattern, injection, text, flags=re.DOTALL)

content = inject_stats(content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied stats filters properly!")
