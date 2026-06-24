import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix d.innings = %s for espn
content = re.sub(r'where_d\.append\("d\.innings = %s"\)', r'where_d.append("d.period = %s")', content)
content = re.sub(r'where_b\.append\("d\.innings = %s"\)', r'where_b.append("d.period = %s")', content)
content = re.sub(r'where_f\.append\("d\.innings = %s"\)', r'where_f.append("d.period = %s")', content)
content = re.sub(r'where_clause\.append\("d\.innings = %s"\)', r'where_clause.append("d.period = %s")', content) # if player.html has it

# In ICC logic, did I use d.innings?
# Wait! In the CTE for ICC, does ICC have innings?
# The table is cricket.icc_json_deliveries
# Let's check where_icc.append("d.innings") or similar.
# In `where_icc`, we probably appended `innings = %s` or `d.innings = %s`.
content = re.sub(r'where_icc\.append\("d\.innings = %s"\)', r'where_icc.append("innings = %s")', content)
content = re.sub(r'where_icc\.append\("innings = %s"\)', r'where_icc.append("innings = %s")', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated innings column references!")
