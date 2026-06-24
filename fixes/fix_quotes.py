import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace any literal backslash escaped quotes with just normal quotes
content = content.replace("\\'%tour%\\'", "'%%tour%%'")
content = content.replace("\\'%series%\\'", "'%%series%%'")
content = content.replace("'%tour%'", "'%%tour%%'")
content = content.replace("'%series%'", "'%%series%%'")

# For the global cache filters() which does NOT use a parameterized execute, %%tour%% will fail.
# So we must revert it back to %tour% there!
# It's in `def filters():` -> `SELECT DISTINCT CASE WHEN l.name ILIKE '%%tour%%' ...`
# Let's use regex to fix it. We know there is only one place where `tournament ILIKE` appears without parameters, but to be safe, I'll just find the exact string.

filters_query = """                cur.execute(\"\"\"
                    SELECT DISTINCT CASE WHEN l.name ILIKE '%%tour%%' OR l.name ILIKE '%%series%%' THEN 'Series' ELSE l.name END as league 
                    FROM cricket.leagues l
                    UNION
                    SELECT DISTINCT CASE WHEN tournament ILIKE '%%tour%%' OR tournament ILIKE '%%series%%' THEN 'Series' ELSE tournament END as league
                    FROM cricket.unified_deliveries
                    WHERE tournament IS NOT NULL AND tournament != ''
                \"\"\")"""

filters_replacement = """                cur.execute(\"\"\"
                    SELECT DISTINCT CASE WHEN l.name ILIKE '%tour%' OR l.name ILIKE '%series%' THEN 'Series' ELSE l.name END as league 
                    FROM cricket.leagues l
                    UNION
                    SELECT DISTINCT CASE WHEN tournament ILIKE '%tour%' OR tournament ILIKE '%series%' THEN 'Series' ELSE tournament END as league
                    FROM cricket.unified_deliveries
                    WHERE tournament IS NOT NULL AND tournament != ''
                \"\"\")"""

content = content.replace(filters_query, filters_replacement)

with open('app.py', 'w') as f:
    f.write(content)
print('Fixed quotes')
