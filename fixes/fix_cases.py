import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's replace ANY sequence that looks like the CASE statement for grouping leagues
target = "CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' ELSE league END"
target2 = "CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN \\\'Series\\\' ELSE league END"
target3 = "CASE WHEN league ILIKE '%tour%' OR league ILIKE '%series%' THEN 'Series' ELSE league END"

replacement = "CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' WHEN league ILIKE '%%asia cup%%' THEN 'Asia Cup' WHEN league ILIKE '%%champions trophy%%' THEN 'Champions Trophy' WHEN league ILIKE '%%world cup%%' THEN 'World Cup' ELSE league END"
replacement2 = "CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN \\\'Series\\\' WHEN league ILIKE '%%asia cup%%' THEN \\\'Asia Cup\\\' WHEN league ILIKE '%%champions trophy%%' THEN \\\'Champions Trophy\\\' WHEN league ILIKE '%%world cup%%' THEN \\\'World Cup\\\' ELSE league END"
replacement3 = "CASE WHEN league ILIKE '%tour%' OR league ILIKE '%series%' THEN 'Series' WHEN league ILIKE '%asia cup%' THEN 'Asia Cup' WHEN league ILIKE '%champions trophy%' THEN 'Champions Trophy' WHEN league ILIKE '%world cup%' THEN 'World Cup' ELSE league END"

c1 = content.count(target)
c2 = content.count(target2)
c3 = content.count(target3)
print(f"Counts: {c1}, {c2}, {c3}")

content = content.replace(target, replacement)
content = content.replace(target2, replacement2)
content = content.replace(target3, replacement3)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated!")
