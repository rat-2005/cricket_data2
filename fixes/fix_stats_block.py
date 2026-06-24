import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_league_conditions(match):
    prefix = match.group(1) # e.g. "where_d"
    param_prefix = match.group(2) # e.g. "params_d"
    return f"""        if league_filter == 'Series':
            {prefix}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%')")
            where_cricsheet.append("(1=1)") # everything else goes to series
            where_icc.append("(tournament NOT ILIKE '%%world cup%%' AND tournament NOT ILIKE '%%world twenty20%%' AND tournament NOT ILIKE '%%t20 world cup%%' AND tournament NOT ILIKE '%%championship%%' AND tournament NOT ILIKE '%%asia cup%%' AND tournament NOT ILIKE '%%champions trophy%%' AND tournament NOT ILIKE '%%premier league%%' AND tournament NOT ILIKE '%%ipl%%' OR tournament IS NULL)")
        elif league_filter == 'World Cup':
            {prefix}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%')")
        elif league_filter == 'Asia Cup':
            {prefix}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%asia cup%%'")
        elif league_filter == 'Champions Trophy':
            {prefix}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%champions trophy%%'")
        elif league_filter == 'Indian Premier League':
            {prefix}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%premier league%%' OR tournament ILIKE '%%ipl%%')")
        else:
            {prefix}.append("1=0")
            where_cricsheet.append("1=0")
            where_icc.append("1=0")"""

# Pattern to find the block:
# It starts with: `if league_filter == 'Series':`
# And ends with: `where_icc.append("1=0")` (Wait, where_icc wasn't there before! The old block ended with `where_cricsheet.append("1=0")`)
# Let's write a robust regex
pattern = r"        if league_filter == 'Series':.*?where_cricsheet\.append\(\"1=0\"\)"

def custom_replace(m):
    block = m.group(0)
    var = 'where_d' if 'where_d' in block else 'where_b' if 'where_b' in block else 'where_f'
    param_var = 'params_d' if 'params_d' in block else 'params_b' if 'params_b' in block else 'params_f'
    
    return f"""        if league_filter == 'Series':
            {var}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%')")
            where_cricsheet.append("(1=1)") # everything else goes to series
            where_icc.append("(tournament NOT ILIKE '%%world cup%%' AND tournament NOT ILIKE '%%world twenty20%%' AND tournament NOT ILIKE '%%t20 world cup%%' AND tournament NOT ILIKE '%%championship%%' AND tournament NOT ILIKE '%%asia cup%%' AND tournament NOT ILIKE '%%champions trophy%%' AND tournament NOT ILIKE '%%premier league%%' AND tournament NOT ILIKE '%%ipl%%' OR tournament IS NULL)")
        elif league_filter == 'World Cup':
            {var}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%')")
        elif league_filter == 'Asia Cup':
            {var}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%asia cup%%'")
        elif league_filter == 'Champions Trophy':
            {var}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
            where_icc.append("tournament ILIKE '%%champions trophy%%'")
        elif league_filter == 'Indian Premier League':
            {var}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
            where_icc.append("(tournament ILIKE '%%premier league%%' OR tournament ILIKE '%%ipl%%')")
        else:
            {var}.append("1=0")
            where_cricsheet.append("1=0")
            where_icc.append("1=0")"""

content = re.sub(pattern, custom_replace, content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated the stats block correctly!")
