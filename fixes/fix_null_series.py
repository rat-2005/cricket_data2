import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_missing_nulls(match):
    prefix = match.group(1) # where_d, where_b, where_f
    # We find the specific NOT ILIKE string and add `OR l.name IS NULL` inside the parenthesis.
    return match.group(0).replace("')\")", "' OR l.name IS NULL)\")")

pattern = r"(where_[dbf])\.append\(\"\(l\.name NOT ILIKE '%%world cup%%' AND l\.name NOT ILIKE '%%world twenty20%%' AND l\.name NOT ILIKE '%%t20 world cup%%' AND l\.name NOT ILIKE '%%championship%%' AND l\.name NOT ILIKE '%%asia cup%%' AND l\.name NOT ILIKE '%%champions trophy%%' AND l\.name NOT ILIKE '%%premier league%%' AND l\.name NOT ILIKE '%%ipl%%'\)\"\)"

new_content = re.sub(pattern, replace_missing_nulls, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Added OR l.name IS NULL to where_[dbf]!")
