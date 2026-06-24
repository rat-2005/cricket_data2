import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_filter_league_block(text, prefix, param_prefix):
    # Notice the trailing space on the 4th line, as seen in the grep output: `where_cricsheet.append("1=0") \n`
    # We will use regex to be safe against trailing whitespace
    pattern = rf"    if league_filter != 'All':\s+{prefix}\.append\(\"l\.name = %s\"\)\s+{param_prefix}\.append\(league_filter\)\s+where_cricsheet\.append\(\"1=0\"\)\s*"
    
    new_block = f"""    if league_filter != 'All':
        if league_filter == 'Series':
            {prefix}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%' OR l.name IS NULL)")
            where_cricsheet.append("(1=1)")
        elif league_filter == 'World Cup':
            {prefix}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
        elif league_filter == 'Asia Cup':
            {prefix}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'Champions Trophy':
            {prefix}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
        elif league_filter == 'Indian Premier League':
            {prefix}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
        else:
            {prefix}.append("1=0")
            where_cricsheet.append("1=0")\n\n"""
            
    return re.sub(pattern, new_block, text)

content = replace_filter_league_block(content, 'where_d', 'params_d')
content = replace_filter_league_block(content, 'where_b', 'params_b')
content = replace_filter_league_block(content, 'where_f', 'params_f')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied filter league blocks!")
