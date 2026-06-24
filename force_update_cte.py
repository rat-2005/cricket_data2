import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any CTE line for leagues in batter_filters, bowler_filters, faceoff_filters
def replace_leagues_array_agg(match):
    # This will match the line generating the leagues array
    # We just want to replace the whole CASE statement logic inside it
    return "array_remove(array_agg(DISTINCT CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup' WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy' WHEN league ILIKE '%%world cup%%' THEN 'World Cup' ELSE league END), NULL) as leagues,"

# Regex to find `array_remove(array_agg(DISTINCT CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN \'Series\' ELSE league END), NULL) as leagues,`
# with or without escaped quotes
regex = r"array_remove\(\s*array_agg\(\s*DISTINCT CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN \\?['\"]Series\\?['\"] ELSE league END\s*\),\s*NULL\s*\)\s*as leagues,"

content = re.sub(regex, replace_leagues_array_agg, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated array_agg logic in app.py!")
