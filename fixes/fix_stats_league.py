import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_league_block(text, prefix, param_prefix):
    old_block = f"""    if league != 'All':
        {prefix}.append("l.name = %s")
        {param_prefix}.append(league)
        where_cricsheet.append("1=0")"""
        
    new_block = f"""    if league != 'All':
        if league == 'Series':
            {prefix}.append("(l.name NOT ILIKE '%%world cup%%' AND l.name NOT ILIKE '%%world twenty20%%' AND l.name NOT ILIKE '%%t20 world cup%%' AND l.name NOT ILIKE '%%championship%%' AND l.name NOT ILIKE '%%asia cup%%' AND l.name NOT ILIKE '%%champions trophy%%' AND l.name NOT ILIKE '%%premier league%%' AND l.name NOT ILIKE '%%ipl%%' OR l.name IS NULL)")
            where_cricsheet.append("(1=1)")
        elif league == 'World Cup':
            {prefix}.append("(l.name ILIKE '%%world cup%%' OR l.name ILIKE '%%world twenty20%%' OR l.name ILIKE '%%t20 world cup%%' OR l.name ILIKE '%%championship%%')")
            where_cricsheet.append("1=0")
        elif league == 'Asia Cup':
            {prefix}.append("l.name ILIKE '%%asia cup%%'")
            where_cricsheet.append("1=0")
        elif league == 'Champions Trophy':
            {prefix}.append("l.name ILIKE '%%champions trophy%%'")
            where_cricsheet.append("1=0")
        elif league == 'Indian Premier League':
            {prefix}.append("(l.name ILIKE '%%premier league%%' OR l.name ILIKE '%%ipl%%')")
            where_cricsheet.append("1=0")
        else:
            {prefix}.append("1=0")
            where_cricsheet.append("1=0")"""
            
    return text.replace(old_block, new_block)

content = replace_league_block(content, 'where_d', 'params_d')
content = replace_league_block(content, 'where_b', 'params_b')
content = replace_league_block(content, 'where_f', 'params_f')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied stats league blocks!")
