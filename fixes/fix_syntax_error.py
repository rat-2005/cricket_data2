import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the exact duplicated blocks and remove them.
# The duplicate starts exactly at:
#             where_icc.append("1=0")
#             where_icc.append("(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%')")
#         elif league_filter == 'Asia Cup':
# down to the next:
#         else:
#             where_d.append("1=0")
#             where_cricsheet.append("1=0")
#             where_icc.append("1=0")

def remove_duplicate(match):
    # Just return the first part: the proper `else` block ending with `where_icc.append("1=0")`
    prefix = match.group(1)
    return f"""        else:
            {prefix}.append("1=0")
            where_cricsheet.append("1=0")
            where_icc.append("1=0")"""

# Pattern to match the bad `else:` block all the way down to the duplicate `where_icc.append("1=0")`
pattern = r"        else:\n            (where_[dbf])\.append\(\"1=0\"\)\n            where_cricsheet\.append\(\"1=0\"\)\n            where_icc\.append\(\"1=0\"\)\n            where_icc\.append\(\"\(tournament ILIKE '%%world cup%%' OR tournament ILIKE '%%world twenty20%%' OR tournament ILIKE '%%t20 world cup%%' OR tournament ILIKE '%%championship%%'\)\"\)\n        elif league_filter == 'Asia Cup':\n            \1\.append\(\"l\.name ILIKE '%%asia cup%%'\"\)\n            where_cricsheet\.append\(\"1=0\"\)\n            where_icc\.append\(\"tournament ILIKE '%%asia cup%%'\"\)\n        elif league_filter == 'Champions Trophy':\n            \1\.append\(\"l\.name ILIKE '%%champions trophy%%'\"\)\n            where_cricsheet\.append\(\"1=0\"\)\n            where_icc\.append\(\"tournament ILIKE '%%champions trophy%%'\"\)\n        elif league_filter == 'Indian Premier League':\n            \1\.append\(\"\(l\.name ILIKE '%%premier league%%' OR l\.name ILIKE '%%ipl%%'\)\"\)\n            where_cricsheet\.append\(\"1=0\"\)\n            where_icc\.append\(\"\(tournament ILIKE '%%premier league%%' OR tournament ILIKE '%%ipl%%'\)\"\)\n        else:\n            \1\.append\(\"1=0\"\)\n            where_cricsheet\.append\(\"1=0\"\)\n            where_icc\.append\(\"1=0\"\)"

new_content = re.sub(pattern, remove_duplicate, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Removed duplicates: {content != new_content}")
