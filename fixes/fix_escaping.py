import re

with open('app.py', 'r') as f:
    content = f.read()

# First, revert the parameters logic
content = content.replace("params_d.extend(['%tour%', '%series%'])", "")
content = content.replace("params_icc_extra.extend(['%tour%', '%series%'])", "")
content = content.replace("params_icc.extend(['%tour%', '%series%'])", "")
content = content.replace("params_d.extend(['%tour%', '%series%', '%tour%', '%series%'])", "")

# Now replace ILIKE %s back to ILIKE '%%tour%%' or ILIKE '%%series%%'
content = content.replace("(l.name ILIKE %s OR l.name ILIKE %s)", "(l.name ILIKE '%%tour%%' OR l.name ILIKE '%%series%%')")
content = content.replace("(tournament ILIKE %s OR tournament ILIKE %s)", "(tournament ILIKE '%%tour%%' OR tournament ILIKE '%%series%%')")

# For the array_agg which I didn't parameterize but it caused the crash:
# array_remove(array_agg(DISTINCT CASE WHEN league ILIKE '%tour%' OR league ILIKE '%series%' THEN 'Series' ELSE league END), NULL) as leagues,
# I need to change '%tour%' to '%%tour%%' and '%series%' to '%%series%%' in the array_agg.
content = content.replace("league ILIKE '%tour%' OR league ILIKE '%series%'", "league ILIKE '%%tour%%' OR league ILIKE '%%series%%'")
# Wait, for the global cache query, it doesn't take parameters, so it doesn't do string formatting?
# Actually, if we pass NO parameters, psycopg2 might not format it. Let's check `def filters()`
# `cur.execute(""" SELECT ... CASE WHEN l.name ILIKE '%tour%' OR l.name ILIKE '%series%' ... """)`
# In psycopg2, if `vars` is not provided (or is None), NO string formatting is performed!
# So the global cache `filters()` which just calls `cur.execute(query)` with NO second argument, DOES NOT NEED `%%`.
# If I replace it with `%%` there, it might send `%%tour%%` to postgres, which searches for literal `%tour%`.
# Let's write the replacement carefully so we only affect where there are parameters.
# The array_agg is inside `batter_filters` and `faceoff_filters` which DO use parameters!
# So in the `query` variable in `batter_filters` and `faceoff_filters`, we DO need `%%tour%%`!
# Let's just do a simple replacement for the array_agg part, and revert the global filters() cache if it gets changed.

# This string only appears in batter_filters and faceoff_filters:
content = content.replace(
    "CASE WHEN league ILIKE '%tour%' OR league ILIKE '%series%' THEN 'Series' ELSE league END",
    "CASE WHEN league ILIKE '%%tour%%' OR league ILIKE '%%series%%' THEN 'Series' ELSE league END"
)

# And what about the WHERE clauses I just reverted to ILIKE '%%tour%%'? That is correct for the parameterized queries.
# Wait, did the global filters() get affected by my first replacements?
# In fix_params.py, I only targeted specific where_d and where_icc blocks. I didn't touch filters().
# So filters() still has ILIKE '%tour%'. Let's verify that.

with open('app.py', 'w') as f:
    f.write(content)

print('Fixed psycopg2 escaping')
