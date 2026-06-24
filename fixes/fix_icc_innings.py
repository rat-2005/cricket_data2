import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix innings = %s to inning_no = %s for where_icc
content = re.sub(r'where_icc\.append\("innings = %s"\)', r'where_icc.append("inning_no = %s")', content)
content = re.sub(r'where_icc\.append\("u\.innings = %s"\)', r'where_icc.append("u.inning_no = %s")', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated ICC innings column reference to inning_no!")
